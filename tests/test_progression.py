import pytest

from cocbot.ocr import DetectedText
from cocbot.progression import (
    Builders,
    Currency,
    UpgradeProposal,
    decide_upgrade,
    parse_amount,
    parse_builders,
    parse_town_hall,
    read_resources,
    read_village_progress,
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
    assert parse_town_hall("Town Hall (Level 13)") == 13


def test_village_text_needs_confident_label_value_pairing():
    progress = read_village_progress(
        [
            DetectedText("Builders", 0.99, (20, 20, 100, 50)),
            DetectedText("2/5", 0.99, (120, 20, 170, 50)),
            DetectedText("Town Hall 13", 0.99, (300, 500, 460, 540)),
        ]
    )
    assert progress.builders == Builders(2, 5)
    assert progress.town_hall == 13
    assert progress.confidence == 1.0
    low = read_village_progress([DetectedText("Town Hall 13", 0.94)])
    assert low.town_hall is None


def test_resources_are_read_only_from_their_right_hand_hud_bands():
    resources = read_resources(
        [
            DetectedText("11 557", 0.82, (1705, 43, 1798, 81)),
            DetectedText("23 500", 0.91, (1689, 148, 1808, 183)),
            DetectedText("369", 0.99, (1742, 242, 1810, 279)),
            DetectedText("999", 0.99, (700, 50, 750, 80)),
        ],
        1920,
        1080,
    )
    assert resources.gold == 11_557
    assert resources.elixir == 23_500
    assert resources.dark_elixir == 369
    assert resources.confidence == 0.82


def test_incomplete_all_zero_hud_fragment_is_not_trusted_as_zero_gold():
    resources = read_resources(
        [
            DetectedText("000", 0.99, (1705, 43, 1798, 81)),
            DetectedText("23 500", 0.99, (1689, 148, 1808, 183)),
        ],
        1920,
        1080,
    )
    assert resources.gold is None
    assert resources.elixir == 23_500


def test_upgrade_is_blocked_until_every_safety_condition_is_verified():
    normal = UpgradeProposal("Archer Tower", Currency.GOLD, 1000)
    assert not decide_upgrade(normal, 2000, Builders(1, 5), 0.94).allowed
    assert not decide_upgrade(normal, 999, Builders(1, 5), 0.99).allowed
    gems = UpgradeProposal("Archer Tower", Currency.GEMS, 1)
    assert not decide_upgrade(gems, 999_999, Builders(5, 5), 1.0).allowed
    assert decide_upgrade(normal, 2000, Builders(1, 5), 0.99).allowed
