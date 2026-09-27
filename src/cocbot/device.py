from __future__ import annotations

import io
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


class DeviceError(RuntimeError):
    pass


@dataclass
class AdbDevice:
    adb_path: str = "adb"
    serial: str | None = None
    timeout: float = 10.0

    def _cmd(self, *args: str, binary: bool = False):
        cmd = [self.adb_path]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += list(args)
        try:
            return subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=self.timeout,
                text=not binary,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            OSError,
        ) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            if isinstance(detail, bytes):
                detail = detail.decode(errors="replace")
            raise DeviceError(
                f"ADB command failed: {' '.join(cmd)}: {detail.strip()}"
            ) from exc

    def connect(self) -> str:
        """Select one device, using MuMu's reported address rather than a fixed port."""
        if self.serial:
            if ":" in self.serial:
                self._cmd("connect", self.serial)
            if not self.ping():
                raise DeviceError(f"Device {self.serial} is not ready")
            return self.serial
        manager = Path(self.adb_path).with_name("MuMuManager.exe")
        if manager.is_file():
            try:
                result = subprocess.run(
                    [str(manager), "info", "-v", "all"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                info = json.loads(result.stdout)
                instances = (
                    info
                    if isinstance(info, list)
                    else ([info] if "index" in info else list(info.values()))
                )
                running = [
                    item
                    for item in instances
                    if isinstance(item, dict)
                    and item.get("is_process_started")
                    and item.get("adb_port")
                ]
                if len(running) > 1:
                    raise DeviceError("Multiple MuMu instances: specify --serial")
                if len(running) == 1:
                    item = running[0]
                    self.serial = (
                        f"{item.get('adb_host_ip') or '127.0.0.1'}:{item['adb_port']}"
                    )
                    return self.connect()
            except (
                subprocess.SubprocessError,
                OSError,
                ValueError,
                TypeError,
                AttributeError,
            ) as exc:
                raise DeviceError(f"Cannot inspect MuMu: {exc}") from exc
        lines = self._cmd("devices").stdout.splitlines()[1:]
        devices = [line.split() for line in lines if line.strip()]
        if len(devices) != 1 or len(devices[0]) < 2 or devices[0][1] != "device":
            raise DeviceError(
                "Expected one ready ADB device; open MuMu or specify --serial"
            )
        self.serial = devices[0][0]
        return self.serial

    def ping(self) -> bool:
        return self._cmd("get-state").stdout.strip() == "device"

    def screenshot(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = self._cmd("exec-out", "screencap", "-p", binary=True)
        try:
            with Image.open(io.BytesIO(result.stdout)) as image:
                if image.format != "PNG":
                    raise ValueError("Expected a PNG screenshot")
                image.verify()
        except (OSError, ValueError) as exc:
            raise DeviceError("ADB returned an invalid screenshot") from exc
        path.write_bytes(result.stdout)
        return path

    def tap(self, x: int, y: int) -> None:
        self._cmd("shell", "input", "tap", str(x), str(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        self._cmd(
            "shell",
            "input",
            "swipe",
            str(x1),
            str(y1),
            str(x2),
            str(y2),
            str(duration_ms),
        )
