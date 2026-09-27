from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

import cv2
import numpy as np

from .ocr import DetectedText, RapidTextReader


class Screen(Enum):
    UNKNOWN = auto()
    POPUP = auto()
    HOME = auto()
    ATTACK_MENU = auto()
    ARMY = auto()
    LABORATORY = auto()
    TOWN_HALL = auto()
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
        cleaned = "".join(
            character if character.isalnum() or character.isspace() else " "
            for character in value.casefold().replace("’", "'")
        )
        return " ".join(cleaned.split())

    def _read(self, image: np.ndarray) -> list[DetectedText]:
        if self._reader:
            return self._reader(image)
        return RapidTextReader().read(image)

    @staticmethod
    def _match(tokens: dict[str, float], phrases: tuple[str, ...]) -> float | None:
        scores = []
        for phrase in phrases:
            matches = [score for token, score in tokens.items() if phrase in token]
            if not matches:
                return None
            scores.append(max(matches))
        return min(scores)

    def _classify(self, image: np.ndarray) -> tuple[Screen, float, str]:
        try:
            texts = self._read(image)
        except RuntimeError as exc:
            return Screen.UNKNOWN, 0.0, str(exc)
        return self._classify_texts(texts)

    def _classify_texts(self, texts: list[DetectedText]) -> tuple[Screen, float, str]:
        tokens = {
            self._normalise(text.value): text.confidence
            for text in texts
            if text.confidence >= 0.75
        }
        popup_rules = (
            ("connection lost", "retry"),
            ("reload game",),
            ("reloadgame",),
            ("anyone there",),
        )
        popup_matches = [
            self._match(tokens, phrases)
            for phrases in popup_rules
            if self._match(tokens, phrases) is not None
        ]
        if popup_matches:
            return (
                Screen.POPUP,
                max(popup_matches),
                "English popup signature matched by live OCR",
            )
        selected_rules = (
            (Screen.LABORATORY, ("laboratory level", "upgrade")),
            (Screen.TOWN_HALL, ("town hall level",)),
        )
        selected_matches = [
            (screen, self._match(tokens, phrases))
            for screen, phrases in selected_rules
            if self._match(tokens, phrases) is not None
        ]
        if len(selected_matches) == 1:
            screen, confidence = selected_matches[0]
            return screen, confidence, "Selected building signature matched by live OCR"
        if len(selected_matches) > 1:
            return Screen.UNKNOWN, 0.0, "Multiple selected-building signatures matched"
        rules = (
            (Screen.HOME, ("attack", "shop")),
            (Screen.ATTACK_MENU, ("find a match", "multiplayer")),
            (Screen.ARMY, ("my army", "saved recipes")),
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

    @staticmethod
    def _decode_png(png: bytes) -> np.ndarray:
        image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode emulator PNG frame")
        return image

    def inspect_png(self, png: bytes) -> tuple[Observation, list[DetectedText]]:
        """Classify one in-memory frame and return its transient OCR results."""
        image = self._decode_png(png)
        height, width = image.shape[:2]
        if (width, height) not in self.supported_resolutions:
            return (
                Observation(
                    Screen.UNKNOWN,
                    width,
                    height,
                    reason="Unsupported emulator resolution",
                ),
                [],
            )
        try:
            texts = self._read(image)
        except RuntimeError as exc:
            return Observation(Screen.UNKNOWN, width, height, reason=str(exc)), []
        screen, confidence, reason = self._classify_texts(texts)
        return Observation(screen, width, height, confidence=confidence, reason=reason), texts

    def observe_png(self, png: bytes) -> Observation:
        return self.inspect_png(png)[0]
