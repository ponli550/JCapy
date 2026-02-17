from textual.screen import ModalScreen
from textual.widgets import OptionList
from jcapy.ui.widgets.kinetic_input import KineticInput
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
            yield KineticInput(placeholder="Type a command...", id="palette-input")
            yield OptionList(*COMMANDS, id="palette-list")

    def on_input_changed(self, event: KineticInput.Changed) -> None:
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

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection."""
        # For now, just print or notify
        # In real implementation, this would trigger the actual command
        selected = str(event.option.prompt)
        cmd_name = selected.split(":")[0].strip()
        self.dismiss(result=cmd_name)
