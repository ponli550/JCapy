from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Action:
    verb: str
    noun: Optional[str] = None
    count: int = 1

class GrammarProcessor:
    """
    NeoVIM-inspired command grammar processor.
    Handles sequences like 'dw', '2dd', 'cw', etc.
    """
    def __init__(self):
        self.partial_verb: Optional[str] = None
        self.count_str: str = ""

        # Verb Mapping
        self.verbs = {
            'd': "delete",
            'c': "change",
            'y': "yank",
            'p': "paste",
        }

        # Noun Mapping
        self.nouns = {
            'w': "word",
            'l': "line",
            'p': "paragraph",
            'b': "block",
            # Doubled verbs usually operate on lines (e.g., dd, yy)
            'd': "line",
            'y': "line",
            'c': "line",
        }

    def process_key(self, key: str) -> Optional[Action]:
        """
        Process a single key stroke and return an Action if a sequence is complete.
        Returns None if the sequence is partial or invalid.
        """
        # 1. Handle counts (e.g., 2dw)
        if key.isdigit():
            self.count_str += key
            return None

        count = int(self.count_str) if self.count_str else 1

        # 2. No active verb yet?
        if not self.partial_verb:
            if key in self.verbs:
                self.partial_verb = key
                return None
            # Not a verb or a count, reset count and return nothing
            self.count_str = ""
            return None

        # 3. We have a verb, looking for a noun
        verb = self.partial_verb
        self.partial_verb = None  # Reset for next sequence
        self.count_str = ""       # Reset for next sequence

        if key in self.nouns:
            # Check for double verb logic (e.g., dd)
            if key == verb or key in self.nouns:
                return Action(verb=self.verbs[verb], noun=self.nouns[key], count=count)

        # Invalid sequence (e.g., 'dx'), reset and return nothing
        return None

    def reset(self):
        """Reset the internal state."""
        self.partial_verb = None
        self.count_str = ""
