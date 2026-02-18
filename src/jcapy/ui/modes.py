from enum import Enum, auto

class InputMode(Enum):
    """JCapy Input Modes for NeoVIM-style interaction."""
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    COMMAND = auto()
    LEADER = auto()
