from __future__ import annotations

import json
import math
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
    confidence: float = 0.0
    reason: str = "No calibrated screen matched"


class Vision:
    def __init__(self, profile: str | Path | None = None):
        self.profile = Path(profile) if profile else None
        self.rules = (
            json.loads(self.profile.read_text(encoding="utf-8"))
            if self.profile
            else None
        )
        self.templates = {}
        if self.rules:
            resolution = self.rules["resolution"]
            if len(resolution) != 2 or any(
                type(value) is not int or value <= 0 for value in resolution
            ):
                raise ValueError("Invalid profile resolution")
            threshold = self.rules.get("threshold", 0.93)
            if (
                not isinstance(threshold, (int, float))
                or not math.isfinite(threshold)
                or not 0.9 <= threshold <= 1
            ):
                raise ValueError("Profile threshold must be between 0.9 and 1")
            for screen, anchors in self.rules["screens"].items():
                if (
                    screen == "UNKNOWN"
                    or screen not in Screen.__members__
                    or len(anchors) < 2
                ):
                    raise ValueError(
                        "Each screen requires at least two independent anchors"
                    )
                if len({tuple(anchor["region"]) for anchor in anchors}) < 2:
                    raise ValueError("Screen anchors must use distinct regions")
                for anchor in anchors:
                    x, y, w, h = anchor["region"]
                    if (
                        any(type(value) is not int for value in (x, y, w, h))
                        or min(x, y) < 0
                        or min(w, h) <= 0
                        or x + w > resolution[0]
                        or y + h > resolution[1]
                    ):
                        raise ValueError(
                            "Anchor lies outside the calibrated resolution"
                        )
                    template = cv2.imread(str(self.profile.parent / anchor["file"]))
                    if template is None or template.std() < 2:
                        raise ValueError(f"Invalid template: {anchor['file']}")
                    self.templates[anchor["file"]] = template

    def observe(self, screenshot: str | Path) -> Observation:
        image = cv2.imread(str(screenshot))
        if image is None:
            raise ValueError(f"Could not read screenshot: {screenshot}")
        height, width = image.shape[:2]
        if self.rules:
            if [width, height] != self.rules["resolution"]:
                return Observation(
                    Screen.UNKNOWN,
                    width,
                    height,
                    reason="Resolution differs from calibration",
                )
            matches = []
            for screen, anchors in self.rules["screens"].items():
                scores = []
                for anchor in anchors:
                    x, y, w, h = anchor["region"]
                    roi = image[y : y + h, x : x + w]
                    template = self.templates[anchor["file"]]
                    if (
                        roi.shape[0] < template.shape[0]
                        or roi.shape[1] < template.shape[1]
                    ):
                        raise ValueError("Template lies outside its search region")
                    result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
                    _, score, _, location = cv2.minMaxLoc(result)
                    tx, ty = location
                    candidate = roi[
                        ty : ty + template.shape[0], tx : tx + template.shape[1]
                    ]
                    # Correlation alone also matches darkened UI behind a modal.
                    if cv2.absdiff(candidate, template).mean() > 15:
                        score = 0.0
                    scores.append(score)
                confidence = min(scores)
                if confidence >= self.rules.get("threshold", 0.93):
                    matches.append((Screen[screen], confidence))
            if len(matches) == 1:
                screen, confidence = matches[0]
                return Observation(
                    screen, width, height, confidence, "All calibrated anchors matched"
                )
            if len(matches) > 1:
                return Observation(
                    Screen.UNKNOWN, width, height, reason="Ambiguous screen matches"
                )
        return Observation(Screen.UNKNOWN, width, height)
