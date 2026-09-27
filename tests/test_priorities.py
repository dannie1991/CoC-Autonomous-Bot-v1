import pytest

from cocbot.priorities import DEFAULT_PRIORITIES, load_priorities, priority_rank


def test_default_priorities_are_ranked_without_side_effects():
    assert priority_rank("Town Hall", DEFAULT_PRIORITIES) == 1
    assert priority_rank("Laboratory", DEFAULT_PRIORITIES) == 2
    assert priority_rank("cannon", DEFAULT_PRIORITIES) is None


def test_custom_priorities_are_validated(tmp_path):
    config = tmp_path / "priorities.yaml"
    config.write_text("priorities:\n  - Cannon\n  - Archer Tower\n", encoding="utf-8")
    assert load_priorities(config) == ("cannon", "archer tower")
    config.write_text("priorities:\n  - Cannon\n  - cannon\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_priorities(config)
