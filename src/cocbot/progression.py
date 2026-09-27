"""Pure parsing and safety rules for future village progression actions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


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
