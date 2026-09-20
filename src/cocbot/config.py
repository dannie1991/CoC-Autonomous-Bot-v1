from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    adb_path: str = os.getenv("COCBOT_ADB_PATH", "adb")
    adb_serial: str | None = os.getenv("COCBOT_ADB_SERIAL")
    screenshot_timeout: float = float(os.getenv("COCBOT_SCREENSHOT_TIMEOUT", "10"))
    poll_interval: float = float(os.getenv("COCBOT_POLL_INTERVAL", "1"))
