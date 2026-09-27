"""Pure parsing and safety rules for future village progression actions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .ocr import DetectedText


class Currency(Enum):
    GOLD = "gold"
    ELIXIR = "elixir"
    DARK_ELIXIR = "dark_elixir"
    GEMS = "gems"


@dataclass(frozen=True)
class Builders:
    free: int
    total: int


@dataclass(frozen=True)
class UpgradeProposal:
    building: str
    currency: Currency
    cost: int


@dataclass(frozen=True)
class UpgradeDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class VillageProgress:
    builders: Builders | None
    town_hall: int | None
    confidence: float


_AMOUNT = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*([kmb])?\s*$", re.IGNORECASE)
_BUILDERS = re.compile(r"\b(\d+)\s*/\s*(\d+)\b")
_TOWN_HALL = re.compile(r"\btown\s*hall\s*(\d+)\b", re.IGNORECASE)


def parse_amount(value: str) -> int | None:
    """Parse English game amounts such as 1,234, 1.2M and 50K."""
    text = value.strip().replace(" ", "")
    match = _AMOUNT.fullmatch(text)
    if not match:
        return None
    number, suffix = match.groups()
    if suffix:
        return int(float(number.replace(",", ".")) * {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suffix.casefold()])
    if "," in number and "." in number:
        number = number.replace(",", "")
    elif "," in number or "." in number:
        separator = "," if "," in number else "."
        left, right = number.split(separator)
        number = left + right if len(right) == 3 else number.replace(separator, ".")
    try:
        return int(float(number))
    except ValueError:
        return None


def parse_builders(value: str) -> Builders | None:
    match = _BUILDERS.search(value)
    if not match:
        return None
    free, total = map(int, match.groups())
    if free > total or total == 0:
        return None
    return Builders(free=free, total=total)


def parse_town_hall(value: str) -> int | None:
    match = _TOWN_HALL.search(value)
    return int(match.group(1)) if match else None


def _nearby_value(label: DetectedText, values: list[DetectedText]) -> DetectedText | None:
    """Return a high-confidence value immediately right of a text label."""
    if label.center is None or label.box is None:
        return None
    _, label_y = label.center
    _, _, label_right, label_bottom = label.box
    label_height = label_bottom - label.box[1]
    candidates = []
    for value in values:
        if value.center is None or value.box is None or value.confidence < 0.95:
            continue
        value_x, value_y = value.center
        if value_x <= label_right or abs(value_y - label_y) > max(24, label_height * 1.5):
            continue
        candidates.append((value_x - label_right, value))
    return min(candidates, default=(0, None), key=lambda candidate: candidate[0])[1]


def read_village_progress(texts: list[DetectedText]) -> VillageProgress:
    """Read only values that OCR can tie to a nearby English label."""
    trusted = [text for text in texts if text.confidence >= 0.95]
    builders = next((parse_builders(text.value) for text in trusted if parse_builders(text.value)), None)
    if builders is None:
        labels = [text for text in trusted if text.value.casefold().strip() == "builders"]
        values = [text for text in trusted if parse_builders(text.value)]
        for label in labels:
            nearby = _nearby_value(label, values)
            if nearby:
                builders = parse_builders(nearby.value)
                break
    town_hall = next((parse_town_hall(text.value) for text in trusted if parse_town_hall(text.value)), None)
    recognised = [value for value in (builders, town_hall) if value is not None]
    confidence = 1.0 if len(recognised) == 2 else (0.95 if recognised else 0.0)
    return VillageProgress(builders=builders, town_hall=town_hall, confidence=confidence)


def decide_upgrade(
    proposal: UpgradeProposal,
    available: int | None,
    builders: Builders | None,
    confidence: float,
) -> UpgradeDecision:
    """Approve only a fully verified normal-resource upgrade.

    This function cannot send input. The action layer must obtain a new live
    observation before it is allowed to tap any button.
    """
    if proposal.currency is Currency.GEMS:
        return UpgradeDecision(False, "Gem spending is permanently blocked")
    if confidence < 0.95:
        return UpgradeDecision(False, "Observation confidence is below 0.95")
    if builders is None or builders.free < 1:
        return UpgradeDecision(False, "No verified free builder")
    if available is None:
        return UpgradeDecision(False, "Available resources are not verified")
    if proposal.cost <= 0:
        return UpgradeDecision(False, "Upgrade cost is invalid")
    if available < proposal.cost:
        return UpgradeDecision(False, "Insufficient verified resources")
    return UpgradeDecision(True, "Upgrade may proceed after a fresh live check")
