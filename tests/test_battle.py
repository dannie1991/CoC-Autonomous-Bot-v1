from cocbot.battle import (
    ArmyStatus,
    Loot,
    LootThresholds,
    evaluate_loot,
    parse_army_capacity,
)


def test_army_capacity_is_ready_only_when_full():
    assert parse_army_capacity("220/220") == ArmyStatus(220, 220)
    assert parse_army_capacity("219 of 220") == ArmyStatus(219, 220)
    assert parse_army_capacity("220/220").ready
    assert not parse_army_capacity("219/220").ready
    assert parse_army_capacity("not readable") == ArmyStatus(None, None)


def test_loot_requires_every_readable_threshold():
    thresholds = LootThresholds(gold=100_000, elixir=50_000, dark_elixir=100)
    accepted = Loot(100_000, 50_000, 100)
    assert evaluate_loot(accepted, thresholds)[0]
    assert not evaluate_loot(Loot(99_999, 50_000, 100), thresholds)[0]
    assert not evaluate_loot(Loot(100_000, None, 100), thresholds)[0]
