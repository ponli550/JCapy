from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, DirectoryTree, Select, Static
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding

class HarvestScreen(Screen):
    """
    Visual Harvest Form.
    Allows user to select a file and enter metadata for a new skill.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    HarvestScreen {
        layout: horizontal;
        background: #1e1e1e;
        color: #c0c0c0;
    }

    #left-pane {
        width: 30%;
        height: 100%;
        border-right: solid #424242;
        padding: 1;
    }

    #right-pane {
        width: 70%;
        height: 100%;
        padding: 2;
    }

    .header {
        text-style: bold;
        color: #007acc;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    Select {
        margin-bottom: 2;
    }

    #file-label {
        color: #fab005;
        margin-bottom: 1;
    }

    .form-group {
        margin-bottom: 2;
    }
    """

    def compose(self) -> ComposeResult:
        # Left Pane: File Browser
        with Container(id="left-pane"):
            yield Label("📁 Select Source File", classes="header")
            yield DirectoryTree(".")

        # Right Pane: Metadata Form
        with Container(id="right-pane"):
            yield Label("🌾 Harvest Metadata", classes="header")

            yield Label("Selected File:", classes="form-group")
            yield Static("No file selected", id="selected-file", classes="file-label")

            yield Label("Skill Name", classes="form-group")
            yield Input(placeholder="e.g. FastAPI Service Template", id="name-input")

            yield Label("Description", classes="form-group")
            yield Input(placeholder="Brief description of what this code does...", id="desc-input")

            yield Label("Quality Grade", classes="form-group")
            yield Select.from_values(["A", "B", "C"], prompt="Select Grade", value="B", id="grade-select")

            yield Button("Harvest Skill", variant="primary", id="submit-btn", disabled=True)
            yield Button("Cancel", variant="error", id="cancel-btn")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from the tree."""
        self.selected_path = str(event.path)

        # Update UI
        file_display = self.query_one("#selected-file", Static)
        file_display.update(f"📄 {event.path.name}")
        file_display.styles.color = "#fab005"

        # Auto-fill name if empty
        name_input = self.query_one("#name-input", Input)
        if not name_input.value:
            # removing extension and replacing underscores/dashes with spaces title case
            clean_name = event.path.stem.replace("_", " ").replace("-", " ").title()
            name_input.value = clean_name

        # Enable submit button
        self.query_one("#submit-btn", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self.submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def submit(self) -> None:
        """Gather data and return to caller."""
        if not hasattr(self, 'selected_path'):
            return

        result = {
            "doc_path": self.selected_path,
            "name": self.query_one("#name-input", Input).value,
            "description": self.query_one("#desc-input", Input).value,
            "grade": self.query_one("#grade-select", Select).value,
        }
        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)
