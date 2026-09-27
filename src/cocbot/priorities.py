"""Configurable, side-effect-free ordering for upgrade proposals."""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_PRIORITIES = (
    "town hall",
    "laboratory",
    "army camp",
    "clan castle",
    "spell factory",
    "barracks",
    "gold storage",
    "elixir storage",
    "dark elixir storage",
    "defence",
)


def load_priorities(path: Path | None = None) -> tuple[str, ...]:
    """Load a user-owned YAML list, rejecting ambiguous configuration."""
    if path is None:
        return DEFAULT_PRIORITIES
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("priorities"), list):
        raise ValueError("Priority file must contain a 'priorities' list")
    priorities = tuple(
        item.strip().casefold()
        for item in data["priorities"]
        if isinstance(item, str) and item.strip()
    )
    if not priorities or len(priorities) != len(data["priorities"]):
        raise ValueError("Every priority must be a non-empty building name")
    if len(set(priorities)) != len(priorities):
        raise ValueError("Priorities must not contain duplicate building names")
    return priorities


def priority_rank(building: str, priorities: tuple[str, ...]) -> int | None:
    """Return a one-based rank, or None when the building is not configured."""
    name = building.strip().casefold()
    try:
        return priorities.index(name) + 1
    except ValueError:
        return None
