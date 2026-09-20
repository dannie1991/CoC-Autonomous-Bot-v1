from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import cv2

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

class Vision:
    def observe(self, screenshot: str | Path) -> Observation:
        image = cv2.imread(str(screenshot))
        if image is None:
            raise ValueError(f"Could not read screenshot: {screenshot}")
        height, width = image.shape[:2]
        # Screen classifiers are intentionally added only after collecting
        # screenshots from the exact emulator resolution used in testing.
        return Observation(Screen.UNKNOWN, width, height)
