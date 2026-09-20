from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            MotionSensor(
                hass.data[DOMAIN][entry.entry_id],
                entry,
            )
        ]
    )


class MotionSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_has_entity_name = True
    _attr_translation_key = "motion"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)

        info = coordinator.data.get("sysinfo", {}).get("system", {})
        identity = (
            info.get("mac")
            or info.get("deviceId")
            or coordinator.api.host
        )

        self._attr_unique_id = f"{identity}_motion"
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
        return bool(self.coordinator.data.get("motion", False))