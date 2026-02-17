# SPDX-License-Identifier: Apache-2.0
import json
import os
from typing import List

class CommandHistoryManager:
    """Manages persistent command history."""

    def __init__(self, history_file: str = None):
        if history_file is None:
            home = os.path.expanduser("~")
            self.history_file = os.path.join(home, ".jcapy", "command_history.json")
        else:
            self.history_file = history_file

        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        self.history: List[str] = self._load_history()

    def _load_history(self) -> List[str]:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self) -> None:
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except IOError:
            pass

    def add_command(self, command: str) -> None:
        """Add command to history, preventing consecutive duplicates."""
        command = command.strip()
        if not command:
            return

        # Prevent duplicates if same as last entry
        if self.history and self.history[-1] == command:
            return

        # Remove previous occurrence to move it to the end (like most shells)
        if command in self.history:
            self.history.remove(command)

        self.history.append(command)

        # Limit history size (e.g., last 1000 commands)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self._save_history()

    def get_history(self) -> List[str]:
        return list(self.history)

    def clear(self) -> None:
        self.history = []
        self._save_history()

# Global instance
HISTORY_MANAGER = CommandHistoryManager()
