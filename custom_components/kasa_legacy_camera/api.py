import base64
import hashlib
import json
import ssl

import aiohttp


class CameraError(Exception):
    """Base exception for Kasa legacy camera communication errors."""


class CameraAuthError(CameraError):
    """Raised when the camera rejects the supplied credentials."""


def _encrypt(data):
    key = 0xAB
    out = bytearray()

    for byte in data:
        encrypted = byte ^ key
        key = encrypted
        out.append(encrypted)

    return bytes(out)


def _decrypt(data):
    key = 0xAB
    out = bytearray()

    for byte in data:
        out.append(byte ^ key)
        key = byte

    return bytes(out)


class CameraApi:
    def __init__(self, session, host, username, password):
        self.session = session
        self.host = host
        self.username = username
        self.password_md5 = hashlib.md5(password.encode()).hexdigest()

        self.ssl = ssl.create_default_context()
        self.ssl.check_hostname = False
        self.ssl.verify_mode = ssl.CERT_NONE

        try:
            self.ssl.set_ciphers("DEFAULT:@SECLEVEL=0")
        except ssl.SSLError:
            pass

    async def _request(self, command, module, method):
        content = base64.b64encode(
            _encrypt(
                json.dumps(
                    command,
                    separators=(",", ":"),
                ).encode()
            )
        ).decode()

        try:
            async with self.session.post(
                f"https://{self.host}:10443/data/LINKIE.json",
                data={"content": content},
                auth=aiohttp.BasicAuth(
                    self.username,
                    self.password_md5,
                ),
                ssl=self.ssl,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (401, 403):
                    raise CameraAuthError("Invalid credentials")

                response.raise_for_status()
                raw = await response.read()

        except CameraAuthError:
            raise
        except (aiohttp.ClientError, TimeoutError, OSError) as err:
            raise CameraError(str(err)) from err

        if not raw:
            raise CameraError("Empty response")

        try:
            decoded = json.loads(
                _decrypt(base64.b64decode(raw)).decode()
            )
            result = decoded[module][method]
        except Exception as err:
            raise CameraError("Invalid camera response") from err

        if result.get("err_code", 0) != 0:
            raise CameraError(str(result))

        return result

    async def get_sysinfo(self):
        command = {
            "system": {
                "get_sysinfo": {}
            }
        }

        return await self._request(
            command,
            "system",
            "get_sysinfo",
        )

    async def set_camera_enabled(self, enabled):
        command = {
            "smartlife.cam.ipcamera.switch": {
                "set_is_enable": {
                    "value": "on" if enabled else "off"
                }
            }
        }

        return await self._request(
            command,
            "smartlife.cam.ipcamera.switch",
            "set_is_enable",
        )