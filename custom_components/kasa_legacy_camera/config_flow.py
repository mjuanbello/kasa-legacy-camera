import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CameraApi, CameraAuthError, CameraError
from .const import (
    CONF_MOTION_HOLD,
    CONF_POLL_INTERVAL,
    DEFAULT_MOTION_HOLD,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)


class CameraConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            api = CameraApi(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                info = await api.get_sysinfo()
            except CameraAuthError:
                errors["base"] = "invalid_auth"
            except CameraError:
                errors["base"] = "cannot_connect"
            else:
                system = info.get("system", {})
                identity = str(
                    system.get("mac")
                    or system.get("deviceId")
                    or host
                )

                await self.async_set_unique_id(identity)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host}
                )

                return self.async_create_entry(
                    title=(
                        f"{system.get('model', 'Kasa Camera')} "
                        f"({host})"
                    ),
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            password = (
                user_input.get(CONF_PASSWORD)
                or entry.data[CONF_PASSWORD]
            )

            api = CameraApi(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_USERNAME],
                password,
            )

            try:
                info = await api.get_sysinfo()
            except CameraAuthError:
                errors["base"] = "invalid_auth"
            except CameraError:
                errors["base"] = "cannot_connect"
            else:
                system = info.get("system", {})
                identity = str(
                    system.get("mac")
                    or system.get("deviceId")
                    or host
                )

                if identity != entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_HOST: host,
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: password,
                        },
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=entry.data[CONF_HOST],
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data[CONF_USERNAME],
                    ): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self._get_reauth_entry()
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._reauth_entry

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            api = CameraApi(
                async_get_clientsession(self.hass),
                entry.data[CONF_HOST],
                username,
                password,
            )

            try:
                info = await api.get_sysinfo()
            except CameraAuthError:
                errors["base"] = "invalid_auth"
            except CameraError:
                errors["base"] = "cannot_connect"
            else:
                system = info.get("system", {})
                identity = str(
                    system.get("mac")
                    or system.get("deviceId")
                    or entry.data[CONF_HOST]
                )

                if identity != entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data[CONF_USERNAME],
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return CameraOptionsFlow(config_entry)


class CameraOptionsFlow(OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_POLL_INTERVAL: user_input[
                        CONF_POLL_INTERVAL
                    ],
                    CONF_MOTION_HOLD: user_input[
                        CONF_MOTION_HOLD
                    ],
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=self._entry.options.get(
                            CONF_POLL_INTERVAL,
                            DEFAULT_POLL_INTERVAL,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=5, max=300),
                    ),
                    vol.Required(
                        CONF_MOTION_HOLD,
                        default=self._entry.options.get(
                            CONF_MOTION_HOLD,
                            DEFAULT_MOTION_HOLD,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=5, max=600),
                    ),
                }
            ),
        )