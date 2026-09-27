"""Pure army and opponent-loot decisions for a future action layer."""

from __future__ import annotations

from dataclasses import dataclass

from .progression import parse_amount


@dataclass(frozen=True)
class ArmyStatus:
    used: int | None
    capacity: int | None

    @property
    def ready(self) -> bool:
        return self.capacity is not None and self.capacity > 0 and self.used == self.capacity


@dataclass(frozen=True)
class Loot:
    gold: int | None
    elixir: int | None
    dark_elixir: int | None


@dataclass(frozen=True)
class LootThresholds:
    gold: int = 100_000
    elixir: int = 100_000
    dark_elixir: int = 0


_SEPARATORS = ("/", "of")


def parse_army_capacity(value: str) -> ArmyStatus:
    """Parse English army capacity text such as ``220/220`` or ``220 of 220``."""
    normalised = value.casefold().replace(" ", "")
    for separator in _SEPARATORS:
        if separator in normalised:
            used, capacity = normalised.split(separator, maxsplit=1)
            if used.isdigit() and capacity.isdigit() and int(capacity) > 0:
                return ArmyStatus(int(used), int(capacity))
    return ArmyStatus(None, None)


def loot_from_text(gold: str, elixir: str, dark_elixir: str) -> Loot:
    """Parse separately positioned opponent-loot OCR strings without guessing."""
    return Loot(parse_amount(gold), parse_amount(elixir), parse_amount(dark_elixir))


def evaluate_loot(loot: Loot, thresholds: LootThresholds) -> tuple[bool, str]:
    """Approve only a fully readable opponent that meets every threshold."""
    values = (loot.gold, loot.elixir, loot.dark_elixir)
    if any(value is None for value in values):
        return False, "Opponent loot is not fully verified"
    if loot.gold < thresholds.gold:
        return False, "Gold loot is below threshold"
    if loot.elixir < thresholds.elixir:
        return False, "Elixir loot is below threshold"
    if loot.dark_elixir < thresholds.dark_elixir:
        return False, "Dark elixir loot is below threshold"
    return True, "Opponent meets every loot threshold"
