from __future__ import annotations

from pathlib import Path

from .config import Settings
from .device import AdbDevice
from .telemetry import event
from .vision import Vision


class Runtime:
    def __init__(self, settings: Settings, profile: str | Path | None = None):
        self.settings = settings
        self.device = AdbDevice(
            settings.adb_path, settings.adb_serial, settings.screenshot_timeout
        )
        self.vision = Vision(profile)

    def probe(self, screenshot_path: str | Path = "artifacts/probe.png"):
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        shot = self.device.screenshot(screenshot_path)
        observation = self.vision.observe(shot)
        event("probe", screenshot=str(shot), observation=observation)
        return observation
