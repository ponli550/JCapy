# SPDX-License-Identifier: Apache-2.0
from textual.widgets import Input
from textual.binding import Binding
from jcapy.core.history import HISTORY_MANAGER
from jcapy.core.plugins import get_registry

class KineticInput(Input):
    """An Input widget with terminal-like history navigation."""

    BINDINGS = [
        Binding("up", "history_up", "Previous Command", show=False),
        Binding("down", "history_down", "Next Command", show=False),
        Binding("tab", "autocomplete", "Autocomplete"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history = []
        self._history_index = -1
        self._current_input = ""

    def on_mount(self) -> None:
        self.refresh_history()

    def refresh_history(self) -> None:
        """Load latest history from manager."""
        self._history = HISTORY_MANAGER.get_history()
        self._history_index = len(self._history)

    def action_history_up(self) -> None:
        """Navigate back in history."""
        if not self._history:
            return

        if self._history_index == len(self._history):
            # Save current input before navigating away
            self._current_input = self.value

        if self._history_index > 0:
            self._history_index -= 1
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)

    def action_history_down(self) -> None:
        """Navigate forward in history."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)
        elif self._history_index == len(self._history) - 1:
            self._history_index += 1
            self.value = self._current_input
            self.cursor_position = len(self.value)
    def action_autocomplete(self) -> None:
        """Simple command autocomplete from registry."""
        val = self.value.strip()
        if not val:
            return

        registry = get_registry()
        commands = list(registry._commands.keys()) + list(registry._aliases.keys())

        matches = [c for c in commands if c.startswith(val)]
        if matches:
            # Pick first match for simplicity
            self.value = matches[0] + " "
            self.cursor_position = len(self.value)
