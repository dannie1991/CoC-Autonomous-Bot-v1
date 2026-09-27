from dataclasses import dataclass
from enum import Enum, auto

import cv2
import numpy as np


class Screen(Enum):
    UNKNOWN = auto()
    HOME = auto()
    ATTACK_MENU = auto()
    SEARCHING = auto()
    BATTLE = auto()
    RESULTS = auto()


@dataclass(frozen=True)
class Observation:
    screen: Screen
    width: int
    height: int
    confidence: float = 0.0
    reason: str = "Screen recognition is not implemented yet"


class Vision:
    """Read transient frames from a running emulator.

    This layer intentionally accepts no account profile, reference screenshots,
    or local calibration. Recognition is added in later modules.
    """

    supported_resolutions = {(1280, 720), (1600, 900), (1920, 1080)}

    def observe_png(self, png: bytes) -> Observation:
        image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode emulator PNG frame")
        height, width = image.shape[:2]
        if (width, height) not in self.supported_resolutions:
            return Observation(
                Screen.UNKNOWN,
                width,
                height,
                reason="Unsupported emulator resolution",
            )
        return Observation(
            Screen.UNKNOWN,
            width,
            height,
            confidence=1.0,
            reason="Live frame received; screen recognition pending",
        )
