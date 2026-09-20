from enum import Enum, auto

class BotState(Enum):
    OBSERVE = auto()
    COLLECT = auto()
    PROGRESS = auto()
    TRAIN = auto()
    SEARCH = auto()
    ATTACK = auto()
    RESULTS = auto()
    RECOVER = auto()
