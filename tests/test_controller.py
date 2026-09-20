from cocbot.controller import Controller
from cocbot.state import BotState


def test_controller_starts_observing():
    assert Controller().tick() is BotState.OBSERVE


def test_controller_transition():
    c = Controller()
    c.transition(BotState.RECOVER)
    assert c.tick() is BotState.RECOVER
