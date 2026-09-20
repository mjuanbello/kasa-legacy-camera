from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CameraApi
from .const import (
    CONF_MOTION_HOLD,
    CONF_POLL_INTERVAL,
    DEFAULT_MOTION_HOLD,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CameraCoordinator


async def async_setup_entry(hass, entry):
    api = CameraApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    coordinator = CameraCoordinator(
        hass,
        api,
        int(
            entry.options.get(
                CONF_POLL_INTERVAL,
                DEFAULT_POLL_INTERVAL,
            )
        ),
        int(
            entry.options.get(
                CONF_MOTION_HOLD,
                DEFAULT_MOTION_HOLD,
            )
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    # Early versions used the camera IP address as the config entry
    # unique ID. Replace it with the camera's persistent identity.
    if entry.unique_id == entry.data[CONF_HOST]:
        system = coordinator.data.get("sysinfo", {}).get("system", {})
        identity = system.get("mac") or system.get("deviceId")

        if identity:
            identity = str(identity)

            for other_entry in hass.config_entries.async_entries(DOMAIN):
                if (
                    other_entry.entry_id != entry.entry_id
                    and other_entry.unique_id == identity
                ):
                    break
            else:
                hass.config_entries.async_update_entry(
                    entry,
                    unique_id=identity,
                )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    entry.async_on_unload(
        entry.add_update_listener(_update_listener)
    )

    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def _update_listener(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)