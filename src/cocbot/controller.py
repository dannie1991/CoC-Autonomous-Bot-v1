from dataclasses import dataclass

from .state import BotState
from .vision import Screen


@dataclass
class Controller:
    state: BotState = BotState.OBSERVE

    def transition(self, next_state: BotState) -> None:
        self.state = next_state

    def tick(self) -> BotState:
        return self.state

    def observe(self, screen: Screen) -> BotState:
        """Advance only the in-memory state; device input belongs to no controller path."""
        if screen in {Screen.UNKNOWN, Screen.POPUP}:
            self.state = BotState.RECOVER
        elif screen in {Screen.HOME, Screen.TOWN_HALL}:
            self.state = BotState.PROGRESS
        elif screen is Screen.ATTACK_MENU:
            self.state = BotState.SEARCH
        elif screen is Screen.ARMY:
            self.state = BotState.SEARCH
        elif screen in {Screen.SEARCHING, Screen.BATTLE}:
            self.state = BotState.ATTACK
        elif screen is Screen.RESULTS:
            self.state = BotState.RESULTS
        return self.state
