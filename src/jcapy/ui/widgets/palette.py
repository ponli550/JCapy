from textual.screen import ModalScreen
from textual.widgets import OptionList, Input
import difflib
from textual.containers import Vertical
from textual.app import ComposeResult
from jcapy.core.plugins import get_registry

def get_available_commands():
    """Fetch commands dynamically from registry."""
    try:
        registry = get_registry()
        # Ensure registry is populated if not already (might need to trigger load_plugins if main hasn't)
        # However, since we run via main.py, it should be loaded.
        cmds = registry.get_commands()
        return [f"{k} : {v}" for k, v in cmds.items()]
    except Exception:
        # Fallback if registry not ready
        return [
            "install : Marketplace",
            "harvest : Create New Skill",
            "apply : Apply Knowledge",
            "list : List Frameworks",
            "manage : Dashboard",
            "doctor : System Health",
            "brainstorm : AI Assistant",
            "explore : Autonomous Research",
            "version : Show Version"
        ]

COMMANDS = get_available_commands()

class CommandPalette(ModalScreen):
    """A modal command palette."""

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Input(placeholder="Type a command...", id="palette-input")
            yield OptionList(*COMMANDS, id="palette-list")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter the list based on input using fuzzy matching."""
        query = event.value.lower()
        if not query:
            filtered = COMMANDS
        else:
            # Fuzzy match descriptions as well
            filtered = [
                cmd for cmd in COMMANDS
                if query in cmd.lower() or difflib.get_close_matches(query, [cmd.split(":")[0].strip()], n=1, cutoff=0.3)
            ]

        opt_list = self.query_one(OptionList)
        opt_list.clear_options()
        opt_list.add_options(filtered)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key on the input field."""
        opt_list = self.query_one(OptionList)
        if opt_list.option_count > 0:
            # If there's a match, use the first one
            selected = str(opt_list.get_option_at_index(0).prompt)
            cmd_name = selected.split(":")[0].strip()
            self.dismiss(result=cmd_name)
        elif event.value.strip():
            # If no match but text exists, try to run text directly
            self.dismiss(result=event.value.strip())

    def on_key(self, event) -> None:
        """Global key handling for the modal."""
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "down":
            self.query_one(OptionList).focus()
        elif event.key == "up":
            # If focus is on list and we hit up at index 0, focus input?
            # Textual handles focus cycling mostly, but let's be explicit if needed.
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection."""
        selected = str(event.option.prompt)
        cmd_name = selected.split(":")[0].strip()
        self.dismiss(result=cmd_name)
