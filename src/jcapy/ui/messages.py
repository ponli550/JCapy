from textual.message import Message
from typing import Any

class ConfigUpdated(Message):
    """Message sent when configuration changes."""
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value
        super().__init__()
