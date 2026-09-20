from datetime import timedelta
import logging
import time

from homeassistant.config_entries import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CameraAuthError, CameraError

_LOGGER = logging.getLogger(__name__)


class CameraCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, poll_interval, motion_hold):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Kasa legacy camera {api.host}",
            update_interval=timedelta(seconds=poll_interval),
        )

        self.api = api
        self.motion_hold = motion_hold
        self._last_activity = None
        self._motion_until = 0.0

    async def _async_update_data(self):
        try:
            info = await self.api.get_sysinfo()
        except CameraAuthError as err:
            raise ConfigEntryAuthFailed(
                "Invalid Kasa credentials"
            ) from err
        except CameraError as err:
            raise UpdateFailed(str(err)) from err

        raw_activity = (
            info.get("system", {})
            .get("last_activity_timestamp")
        )

        try:
            activity = (
                int(raw_activity)
                if raw_activity is not None
                else None
            )
        except (TypeError, ValueError):
            activity = None

        if self._last_activity is None:
            self._last_activity = activity
        elif (
            activity is not None
            and activity != self._last_activity
        ):
            self._last_activity = activity
            self._motion_until = (
                time.monotonic() + self.motion_hold
            )

        return {
            "motion": time.monotonic() < self._motion_until,
            "last_activity_timestamp": activity,
            "sysinfo": info,
        }