from types import SimpleNamespace
from unittest.mock import Mock

from cocbot.progression import Builders, Resources, VillageProgress
from cocbot.runtime import Runtime
from cocbot.vision import Observation, Screen


def test_action_gate_blocks_incomplete_or_uncertain_live_data():
    observation = Observation(Screen.HOME, 1920, 1080, confidence=0.84)
    progress = VillageProgress(
        Builders(2, 2),
        10,
        1.0,
        Resources(100, 100, 100, 1.0),
    )
    allowed, reason = Runtime.action_gate(observation, progress)
    assert not allowed
    assert "confidence" in reason


def test_action_gate_requires_complete_verified_home_observation():
    observation = Observation(Screen.HOME, 1920, 1080, confidence=0.99)
    progress = VillageProgress(
        Builders(2, 2),
        10,
        1.0,
        Resources(100, 100, 100, 0.84),
    )
    assert not Runtime.action_gate(observation, progress)[0]
    complete = SimpleNamespace(
        confidence=1.0,
        resources=Resources(100, 100, 100, 1.0),
    )
    assert Runtime.action_gate(observation, complete) == (
        True,
        "Live HOME observation is complete",
    )


def test_action_gate_requires_readable_gold_and_elixir_values():
    observation = Observation(Screen.HOME, 1920, 1080, confidence=0.99)
    progress = VillageProgress(
        Builders(2, 2), 10, 1.0, Resources(None, 100, 100, 0.99)
    )
    assert not Runtime.action_gate(observation, progress)[0]


def test_open_attack_menu_dry_run_uses_one_live_ocr_target():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=1, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    home = Observation(Screen.HOME, 1920, 1080, confidence=0.99)
    attack = SimpleNamespace(value="Attack!", confidence=0.99, center=(100.4, 200.6))
    runtime.vision.inspect_png = Mock(return_value=(home, [attack]))
    runtime.vision._normalise = Mock(return_value="attack")

    result = runtime.open_attack_menu()

    assert result == {
        "executed": False,
        "plan": {"label": "Attack", "x": 100, "y": 127, "confidence": 0.99},
    }
    runtime.device.tap.assert_not_called()


def test_open_attack_menu_requires_post_tap_attack_menu_confirmation():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    attack = SimpleNamespace(value="Attack", confidence=0.99, center=(100, 200))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), [attack]),
            (Observation(Screen.ATTACK_MENU, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="attack")

    assert runtime.open_attack_menu(execute=True)["screen"] == "ATTACK_MENU"
    runtime.device.tap.assert_called_once_with(100, 127)


def test_reload_after_inactivity_requires_popup_then_home_confirmation():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    reload_button = SimpleNamespace(value="Reload Game", confidence=0.99, center=(700, 600))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.POPUP, 1920, 1080, confidence=0.99), [reload_button]),
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="reloadgame")

    assert runtime.reload_after_inactivity(execute=True)["screen"] == "HOME"
    runtime.device.tap.assert_called_once_with(700, 600)


def test_reload_after_inactivity_waits_through_a_loading_screen():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    reload_button = SimpleNamespace(value="Reload Game", confidence=0.99, center=(700, 600))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.POPUP, 1920, 1080, confidence=0.99), [reload_button]),
            (Observation(Screen.UNKNOWN, 1920, 1080, confidence=0.0), []),
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="reloadgame")

    assert runtime.reload_after_inactivity(execute=True)["screen"] == "HOME"


def test_find_match_requires_attack_menu_then_army_confirmation():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    find = SimpleNamespace(value="Find a Match", confidence=0.99, center=(400, 760))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.ATTACK_MENU, 1920, 1080, confidence=0.99), [find]),
            (Observation(Screen.ARMY, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="find a match")

    assert runtime.find_match(execute=True)["screen"] == "ARMY"
    runtime.device.tap.assert_called_once_with(400, 760)


def test_start_matchmaking_accepts_battle_after_my_army():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    attack = SimpleNamespace(value="Attack!", confidence=0.99, center=(1700, 960))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.ARMY, 1920, 1080, confidence=0.99), [attack]),
            (Observation(Screen.BATTLE, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="attack")

    assert runtime.start_matchmaking(execute=True)["screen"] == "BATTLE"
    runtime.device.tap.assert_called_once_with(1700, 960)


def test_return_home_requires_results_then_home_confirmation():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    home = SimpleNamespace(value="Return Home", confidence=0.99, center=(960, 930))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.RESULTS, 1920, 1080, confidence=0.99), [home]),
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="return home")

    assert runtime.return_home(execute=True)["screen"] == "HOME"
    runtime.device.tap.assert_called_once_with(960, 930)


def test_return_home_requests_recovery_when_game_shows_popup():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    home = SimpleNamespace(value="Return Home", confidence=0.99, center=(960, 930))
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.RESULTS, 1920, 1080, confidence=0.99), [home]),
            (Observation(Screen.POPUP, 1920, 1080, confidence=0.99), []),
        ]
    )
    runtime.vision._normalise = Mock(return_value="return home")

    result = runtime.return_home(execute=True)

    assert result["recovery_required"]
    assert result["screen"] == "POPUP"


def test_collect_once_requires_indicator_change_after_tap():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    collect = SimpleNamespace(value="Collect", confidence=0.99, center=(220, 330))
    before = [collect]
    after = []
    runtime.vision.inspect_png = Mock(
        side_effect=[
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), before),
            (Observation(Screen.HOME, 1920, 1080, confidence=0.99), after),
        ]
    )
    runtime.vision._normalise = Mock(return_value="collect")

    assert runtime.collect_once(execute=True)["indicator_cleared"]
    runtime.device.tap.assert_called_once_with(220, 373)


def test_collect_once_uses_loot_cart_button_centre_for_low_screen_labels():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    collect = SimpleNamespace(value="Collect", confidence=0.99, center=(960, 890))
    runtime.vision.inspect_png = Mock(
        return_value=(Observation(Screen.HOME, 1920, 1080, confidence=0.99), [collect])
    )
    runtime.vision._normalise = Mock(return_value="collect")

    result = runtime.collect_once()

    assert result["plan"]["y"] == 841
    runtime.device.tap.assert_not_called()


def test_laboratory_upgrade_plan_pairs_cost_above_upgrade_button():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    texts = [
        SimpleNamespace(value="Upgrade", confidence=0.99, center=(1080, 890)),
        SimpleNamespace(value="12 500", confidence=0.99, center=(1080, 775)),
        SimpleNamespace(value="2/2", confidence=0.99, center=(980, 60)),
        SimpleNamespace(value="23 500", confidence=0.99, center=(1750, 165)),
    ]
    runtime.vision.inspect_png = Mock(
        return_value=(Observation(Screen.LABORATORY, 1920, 1080, confidence=0.99), texts)
    )
    runtime.vision._normalise = Mock(
        side_effect=lambda text: "upgrade" if text == "Upgrade" else text.casefold()
    )

    result = runtime.laboratory_upgrade_plan()

    assert result["proposal"].cost == 12_500
    assert result["available"] == 23_500
    assert result["allowed"]


def test_town_hall_status_reports_construction_without_input():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    texts = [
        SimpleNamespace(value="Town Hall (Level 3)", confidence=0.99, center=(960, 720)),
        SimpleNamespace(value="Cancel", confidence=0.99, center=(640, 850)),
    ]
    runtime.vision.inspect_png = Mock(
        return_value=(Observation(Screen.TOWN_HALL, 1920, 1080, confidence=0.99), texts)
    )
    runtime.vision._normalise = Mock(side_effect=lambda text: text.casefold().replace("(", "").replace(")", ""))

    result = runtime.town_hall_status()

    assert result == {
        "town_hall": 3,
        "under_construction": True,
        "upgrade_available": False,
        "input_actions": 0,
    }
    runtime.device.tap.assert_not_called()


def test_town_hall_status_reads_a_live_screen_confidence_level():
    runtime = Runtime(SimpleNamespace(screenshot_timeout=1, poll_interval=0.01, adb_path="adb", adb_serial=None))
    runtime.device = Mock()
    runtime.device.ping.return_value = True
    runtime.device.screenshot_png.return_value = b"frame"
    texts = [SimpleNamespace(value="Town Hall (Level 3)", confidence=0.88, center=(960, 720))]
    runtime.vision.inspect_png = Mock(
        return_value=(Observation(Screen.TOWN_HALL, 1920, 1080, confidence=0.88), texts)
    )
    runtime.vision._normalise = Mock(return_value="town hall level 3")

    assert runtime.town_hall_status()["town_hall"] == 3
