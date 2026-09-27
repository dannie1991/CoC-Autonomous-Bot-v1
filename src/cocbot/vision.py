from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

import cv2
import numpy as np

from .ocr import DetectedText, RapidTextReader


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

    def __init__(self, reader: Callable[[np.ndarray], list[DetectedText]] | None = None):
        self._reader = reader

    @staticmethod
    def _normalise(value: str) -> str:
        return " ".join(value.casefold().replace("’", "'").split())

    def _read(self, image: np.ndarray) -> list[DetectedText]:
        if self._reader:
            return self._reader(image)
        return RapidTextReader().read(image)

    @staticmethod
    def _match(tokens: dict[str, float], phrases: tuple[str, ...]) -> float | None:
        if any(phrase not in tokens for phrase in phrases):
            return None
        return min(tokens[phrase] for phrase in phrases)

    def _classify(self, image: np.ndarray) -> tuple[Screen, float, str]:
        try:
            texts = self._read(image)
        except RuntimeError as exc:
            return Screen.UNKNOWN, 0.0, str(exc)
        tokens = {
            self._normalise(text.value): text.confidence
            for text in texts
            if text.confidence >= 0.75
        }
        rules = (
            (Screen.HOME, ("attack", "shop")),
            (Screen.ATTACK_MENU, ("find a match", "multiplayer")),
            (Screen.SEARCHING, ("searching for opponents",)),
            (Screen.BATTLE, ("end battle",)),
            (Screen.RESULTS, ("return home",)),
        )
        matches = [
            (screen, self._match(tokens, phrases))
            for screen, phrases in rules
            if self._match(tokens, phrases) is not None
        ]
        if len(matches) != 1:
            return Screen.UNKNOWN, 0.0, "No unique supported screen signature"
        screen, confidence = matches[0]
        return screen, confidence, "English UI signature matched by live OCR"

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
        screen, confidence, reason = self._classify(image)
        return Observation(screen, width, height, confidence=confidence, reason=reason)
