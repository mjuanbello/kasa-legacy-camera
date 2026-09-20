from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            CameraSwitch(
                hass.data[DOMAIN][entry.entry_id],
                entry,
            )
        ]
    )


class CameraSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "camera"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)

        info = coordinator.data.get("sysinfo", {}).get("system", {})
        identity = (
            info.get("mac")
            or info.get("deviceId")
            or coordinator.api.host
        )

        self._attr_unique_id = f"{identity}_camera_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(identity))},
            name=entry.title,
            manufacturer="TP-Link",
            model=info.get("model", "Kasa Camera"),
            sw_version=info.get("sw_ver"),
            hw_version=info.get("hw_ver"),
        )

    @property
    def is_on(self):
        info = self.coordinator.data.get("sysinfo", {}).get("system", {})
        return info.get("camera_switch") == "on"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.set_camera_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.set_camera_enabled(False)
        await self.coordinator.async_request_refresh()