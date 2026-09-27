from __future__ import annotations

from .config import Settings
from .device import AdbDevice
from .telemetry import event
from .vision import Vision


class Runtime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = AdbDevice(
            settings.adb_path, settings.adb_serial, settings.screenshot_timeout
        )
        self.vision = Vision()

    def probe(self):
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation = self.vision.observe_png(self.device.screenshot_png())
        event("probe", observation=observation, frame_saved=False)
        return observation
