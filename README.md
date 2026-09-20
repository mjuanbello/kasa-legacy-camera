# Kasa Legacy Camera

A custom Home Assistant integration for selected legacy TP-Link Kasa cameras using their local LINKIE interface.

The integration communicates directly with the camera over the local network. No TP-Link/Kasa cloud connection is required for the currently implemented features.

## Tested cameras

The integration has been tested with:

| Model | Hardware / region | Status |
| --- | --- | --- |
| TP-Link Kasa KC110 | KC110(UN) v1.0 | Tested |
| TP-Link Kasa KC200 | KC200(EU) v1.0 | Tested |

Other legacy Kasa camera models may use a compatible LINKIE interface, but they have not been tested.

Compatibility with an unlisted model should therefore not be assumed.

## Features

### Local camera enable/disable

Home Assistant exposes a `switch` entity that reflects and controls the camera's enabled state.

The current state is obtained locally from:

`system.get_sysinfo` → `camera_switch`

Camera enable/disable commands use the local LINKIE method:

`smartlife.cam.ipcamera.switch.set_is_enable`

with:

- `on` to enable the camera
- `off` to disable the camera

This functionality has been tested successfully on both KC110 and KC200.

### Motion detection

Home Assistant exposes a motion `binary_sensor`.

These legacy cameras do not expose a conventional motion entity through the interface currently used by this integration. Instead, motion detection is derived from:

`system.get_sysinfo` → `system.last_activity_timestamp`

A change in this timestamp is interpreted as camera activity and activates the motion sensor for a configurable period.

The first value obtained after startup is used as a baseline and does not generate a false motion event.

The default motion hold time is 30 seconds.

> [!NOTE]
> This is an inferred motion state based on changes to `last_activity_timestamp`, rather than direct access to the camera's internal motion detector.

The integration deliberately does not force the motion sensor to `off` when the camera reports `camera_switch: off`. If the activity timestamp changes unexpectedly while the camera is disabled, that change remains visible to Home Assistant rather than being suppressed.

## Local communication

Communication with the camera uses HTTPS on TCP port `10443`:

`https://CAMERA_IP:10443/data/LINKIE.json`

Requests use:

- HTTP Basic authentication
- Kasa username
- lowercase hexadecimal MD5 representation of the Kasa password
- LINKIE XOR encoding
- Base64 encoding

The integration communicates directly between Home Assistant and the camera on the local network.

No external Python packages are required.

## Installation

Copy the `kasa_legacy_camera` directory into your Home Assistant custom components directory:

```text
/config/custom_components/kasa_legacy_camera/
```

The resulting structure should include:

```text
custom_components/
└── kasa_legacy_camera/
   ├── __init__.py
   ├── api.py
   ├── binary_sensor.py
   ├── config_flow.py
   ├── const.py
   ├── coordinator.py
   ├── manifest.json
   ├── strings.json
   ├── switch.py
   └── translations/
       ├── en.json
       └── es.json
```

Restart Home Assistant after installation.

Then go to:

**Settings → Devices & services → Add integration**

and search for:

**Kasa Legacy Camera**

## Initial configuration

Each camera is configured as a separate Home Assistant config entry.

You will need:

- Camera IP address
- Kasa username
- Kasa password

The integration connects to the camera locally and retrieves its system information before creating the entry.

The camera MAC address is used as the preferred persistent identity. `deviceId` is used as a fallback when available.

This prevents the Home Assistant identity of a camera from depending on its IP address.

Using DHCP reservations or otherwise keeping camera addresses predictable is still recommended.

## Reconfiguration

Connection settings can be changed through the integration's **Reconfigure** flow.

It allows changing:

- IP address
- Kasa username
- Kasa password

The password field can be left blank to retain the currently stored password.

Before accepting a new address or credentials, the integration connects to the camera and verifies that its persistent identity matches the existing Home Assistant config entry.

This prevents accidentally replacing one configured camera with another camera located at a different IP address.

## Options

The integration currently provides two configurable options:

### Polling interval

Default:

```text
15 seconds
```

Allowed range:

```text
5–300 seconds
```

This controls how often Home Assistant requests system information from the camera.

### Motion hold time

Default:

```text
30 seconds
```

Allowed range:

```text
5–600 seconds
```

This controls how long the Home Assistant motion entity remains active after a change in `last_activity_timestamp` is detected.

## Authentication failures

The integration distinguishes authentication failures from ordinary communication failures.

Network errors, timeouts, or an unavailable camera are treated as temporary update failures.

Rejected Kasa credentials are treated as authentication failures so that Home Assistant can request reauthentication.

The reauthentication flow allows new Kasa credentials to be supplied without recreating the camera entry.

## Entities

Each configured camera currently creates:

| Entity | Type | Purpose |
| --- | --- | --- |
| Motion | `binary_sensor` | Activity inferred from `last_activity_timestamp` |
| Camera | `switch` | Local camera enable/disable control |

Entity names are translated. English and Spanish translations are currently included.

## Upgrading from early development versions

Early development versions of this integration could use the camera IP address as the Home Assistant config entry `unique_id`.

Current versions use a persistent camera identity, preferably its MAC address.

When an old IP-based entry is detected, the integration attempts to migrate it automatically after successfully communicating with the camera.

Existing entity unique IDs are based on the same persistent camera identity.

## Limitations

This integration currently does **not** provide:

- Live video streaming
- Recorded video
- Still-image camera entities
- Audio
- Pan/tilt control
- Camera configuration such as sensitivity or detection zones
- Cloud event history
- Direct access to the camera's internal motion detector

Motion detection is inferred from `last_activity_timestamp`.

The integration has only been tested on the camera models explicitly listed above.

## Security considerations

The cameras use a legacy local protocol and HTTPS implementation.

To communicate with them, the integration must accommodate the TLS behaviour supported by these older devices.

The camera's HTTPS certificate is therefore not validated in the same way as a modern public HTTPS service.

This integration is intended for cameras connected to a trusted local network.

Kasa credentials are stored in the Home Assistant config entry because they are required for subsequent local authentication with the camera.

## Troubleshooting

### Cannot connect to the camera

Check that:

- Home Assistant can reach the camera IP address
- the camera and Home Assistant are on networks that allow direct communication
- TCP port `10443` is reachable
- the camera is powered and responsive

### Invalid username or password

Verify the Kasa credentials used by the camera.

The integration validates the credentials directly against the local camera interface.

### Camera IP address changed

Use the integration's **Reconfigure** flow and enter the new IP address.

The integration verifies the physical identity of the camera before updating the stored address.

### Motion events are delayed

Motion detection is polling based.

With the default 15-second polling interval, Home Assistant may detect a timestamp change several seconds after the camera itself detected the activity.

Reducing the polling interval can reduce this delay at the cost of more frequent requests to the camera.

## Diagnostics and bug reports

When reporting a problem, useful information includes:

- Camera model
- Hardware version
- Firmware version
- Home Assistant version
- Whether camera enable/disable works
- Whether `last_activity_timestamp` changes when motion occurs
- Relevant Home Assistant log messages

Do **not** publish Kasa passwords or other credentials in bug reports.

## Project status

This project exists to provide local Home Assistant support for legacy Kasa cameras that are not fully supported by current integrations.

Version 0.2.0 has been functionally tested with:

- TP-Link Kasa KC110(UN)
- TP-Link Kasa KC200(EU)

The implementation should be considered model-specific unless compatibility with additional cameras is independently verified.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
