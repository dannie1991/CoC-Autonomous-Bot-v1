import pytest

from cocbot.progression import (
    Builders,
    Currency,
    UpgradeProposal,
    decide_upgrade,
    parse_amount,
    parse_builders,
    parse_town_hall,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("1,234", 1234), ("1.234", 1234), ("1.2M", 1_200_000), ("50K", 50_000)],
)
def test_parse_amount(text, expected):
    assert parse_amount(text) == expected


def test_parse_progression_values():
    assert parse_builders("Builders: 2 / 5") == Builders(free=2, total=5)
    assert parse_builders("6/5") is None
    assert parse_town_hall("Town Hall 13") == 13


def test_upgrade_is_blocked_until_every_safety_condition_is_verified():
    normal = UpgradeProposal("Archer Tower", Currency.GOLD, 1000)
    assert not decide_upgrade(normal, 2000, Builders(1, 5), 0.94).allowed
    assert not decide_upgrade(normal, 999, Builders(1, 5), 0.99).allowed
    gems = UpgradeProposal("Archer Tower", Currency.GEMS, 1)
    assert not decide_upgrade(gems, 999_999, Builders(5, 5), 1.0).allowed
    assert decide_upgrade(normal, 2000, Builders(1, 5), 0.99).allowed
