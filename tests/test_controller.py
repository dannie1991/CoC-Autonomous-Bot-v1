from cocbot.controller import Controller
from cocbot.state import BotState
from cocbot.vision import Screen


def test_controller_starts_observing():
    assert Controller().tick() is BotState.OBSERVE


def test_controller_transition():
    c = Controller()
    c.transition(BotState.RECOVER)
    assert c.tick() is BotState.RECOVER


def test_controller_only_advances_its_in_memory_state_from_observations():
    controller = Controller()
    assert controller.observe(Screen.HOME) is BotState.PROGRESS
    assert controller.observe(Screen.ATTACK_MENU) is BotState.SEARCH
    assert controller.observe(Screen.ARMY) is BotState.SEARCH
    assert controller.observe(Screen.BATTLE) is BotState.ATTACK
    assert controller.observe(Screen.RESULTS) is BotState.RESULTS


def test_popup_and_unknown_screens_stop_the_normal_flow():
    controller = Controller()
    assert controller.observe(Screen.POPUP) is BotState.RECOVER
    assert controller.observe(Screen.UNKNOWN) is BotState.RECOVER
