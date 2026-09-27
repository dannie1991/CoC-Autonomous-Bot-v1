import math
import os
from dataclasses import dataclass, field


def default_adb() -> str:
    from pathlib import Path

    candidate = (
        Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        / "Netease/MuMuPlayer/nx_main/adb.exe"
    )
    return os.getenv("COCBOT_ADB_PATH") or (
        str(candidate) if candidate.is_file() else "adb"
    )


@dataclass(frozen=True)
class Settings:
    adb_path: str = field(default_factory=default_adb)
    adb_serial: str | None = field(
        default_factory=lambda: os.getenv("COCBOT_ADB_SERIAL") or None
    )
    screenshot_timeout: float = field(
        default_factory=lambda: float(os.getenv("COCBOT_SCREENSHOT_TIMEOUT", "10"))
    )
    poll_interval: float = field(
        default_factory=lambda: float(os.getenv("COCBOT_POLL_INTERVAL", "1"))
    )

    def __post_init__(self):
        for name in ("screenshot_timeout", "poll_interval"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
