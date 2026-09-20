from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path

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
            return subprocess.run(cmd, check=True, capture_output=True,
                                  timeout=self.timeout,
                                  text=not binary)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            raise DeviceError(f"ADB command failed: {' '.join(cmd)}") from exc

    def ping(self) -> bool:
        return self._cmd("get-state").stdout.strip() == "device"

    def screenshot(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = self._cmd("exec-out", "screencap", "-p", binary=True)
        path.write_bytes(result.stdout)
        return path

    def tap(self, x: int, y: int) -> None:
        self._cmd("shell", "input", "tap", str(x), str(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        self._cmd("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))
