from dataclasses import dataclass

from .state import BotState


@dataclass
class Controller:
    state: BotState = BotState.OBSERVE

    def transition(self, next_state: BotState) -> None:
        self.state = next_state

    def tick(self) -> BotState:
        return self.state
