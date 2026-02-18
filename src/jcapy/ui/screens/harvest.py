from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Input, Button, Label, DirectoryTree, Select, Static, TextArea, Switch
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from textual.binding import Binding
from textual.worker import work
import os
from jcapy.services.frameworks.engine import FrameworkEngine
from jcapy.models.frameworks import ResultStatus

class HarvestSuccessScreen(ModalScreen):
    """Cinematic success screen after harvesting."""

    DEFAULT_CSS = """
    HarvestSuccessScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.8);
    }

    #success-panel {
        width: 60;
        height: auto;
        padding: 2;
        border: thick $success;
        background: $surface;
        align: center middle;
    }

    .title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    .skill-name {
        color: cyan;
        text-style: italic;
        margin-bottom: 2;
    }

    .btn-group {
        width: 1fr;
        height: auto;
        margin-top: 1;
    }

    Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, skill_name: str, framework_id: str):
        self.skill_name = skill_name
        self.framework_id = framework_id
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="success-panel"):
            yield Label("✅ Skill Harvested Successfully!", classes="title")
            yield Label(f"'{self.skill_name}'", classes="skill-name")

            with Horizontal(classes="btn-group"):
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Push", variant="secondary", id="push")
                yield Button("Edit", id="edit")

            yield Button("Done", id="done", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action = event.button.id
        if action == "done":
            self.dismiss()
        elif action == "apply":
            self.app.run_command(f"apply {self.framework_id} --dry-run")
            self.dismiss()
        elif action == "push":
            self.app.run_command(f"push {self.framework_id}")
            self.dismiss()
        elif action == "edit":
            self.app.run_command(f"open {self.framework_id}")
            self.dismiss()

class HarvestScreen(Screen):
    """
    Visual Harvest Form (Single Page).
    Allows user to select a file and enter metadata for a new skill.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Save Framework"),
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
        padding: 1 2;
    }

    .header {
        text-style: bold;
        color: #007acc;
        margin-bottom: 1;
    }

    Input, Select, TextArea {
        margin-bottom: 1;
    }

    #selected-file-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: #252525;
        border: thin #424242;
    }

    .file-label {
        color: #fab005;
        text-style: bold;
    }

    .form-group {
        margin-bottom: 0;
        text-style: dim;
        color: #888;
    }

    #submit-btn {
        margin-top: 1;
        width: 100%;
    }

    #cancel-btn {
        width: 100%;
        margin-top: 1;
    }

    TextArea {
        height: 15;
        border: solid #424242;
    }

    #form-scroll {
        height: 1fr;
        padding-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        # Left Pane: File Browser
        with Container(id="left-pane"):
            yield Label("📁 Select Source", classes="header")
            yield DirectoryTree(".")

        # Right Pane: Metadata Form
        with Container(id="right-pane"):
            yield Label("🌾 Harvest Metadata", classes="header")

            with Container(id="selected-file-container"):
                yield Horizontal(
                    Label("Source: "),
                    Static("No file selected", id="selected-file", classes="file-label"),
                )

            with VerticalScroll(id="form-scroll"):
                yield Label("Skill Name", classes="form-group")
                yield Input(placeholder="e.g. FastAPI Service Template", id="name-input")

                yield Label("Description", classes="form-group")
                yield Input(placeholder="Brief description of what this code does...", id="desc-input")

                with Horizontal(classes="form-group"):
                    with Vertical():
                        yield Label("Domain")
                        yield Select.from_values(["misc", "ui", "backend", "devops"], prompt="Select Domain", value="misc", id="domain-select")
                    with Vertical():
                        yield Label("Grade")
                        yield Select.from_values(["A", "B", "C"], prompt="Select Grade", value="B", id="grade-select")

                yield Label("Pros (comma separated)", classes="form-group")
                yield Input(placeholder="Fast, Robust, Standard...", id="pros-input")

                yield Label("Cons (comma separated)", classes="form-group")
                yield Input(placeholder="Heavy, Legacy...", id="cons-input")

                yield Label("Code Snippet / Execution Block", classes="form-group")
                yield TextArea(id="snippet-area", language="python")

                yield Button("🌾 Harvest Skill (Ctrl+S)", variant="primary", id="submit-btn", disabled=True)
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
            clean_name = event.path.stem.replace("_", " ").replace("-", " ").title()
            name_input.value = clean_name

        # Populating Snippet Area
        try:
            with open(self.selected_path, 'r') as f:
                content = f.read()
                snippet_area = self.query_one("#snippet-area", TextArea)
                snippet_area.text = content

                # Set language based on extension
                ext = event.path.suffix.lower()
                lang_map = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".sh": "bash",
                    ".md": "markdown",
                    ".json": "json",
                    ".yaml": "yaml",
                }
                snippet_area.language = lang_map.get(ext, "python")
        except:
            pass

        # Enable submit button
        self.query_one("#submit-btn", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self.submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def submit(self) -> None:
        """Gather data and initiate save lifecycle."""
        if not hasattr(self, 'selected_path'):
            return

        metadata = {
            "doc_path": self.selected_path,
            "name": self.query_one("#name-input", Input).value.strip(),
            "description": self.query_one("#desc-input", Input).value.strip(),
            "grade": self.query_one("#grade-select", Select).value,
            "domain": self.query_one("#domain-select", Select).value,
            "pros": self.query_one("#pros-input", Input).value.strip(),
            "cons": self.query_one("#cons-input", Input).value.strip(),
            "snippet": self.query_one("#snippet-area", TextArea).text,
        }

        if not metadata["name"]:
            self.app.notify("Skill name is required.", severity="error")
            return

        # 1. Check for Overwrite
        from jcapy.commands.frameworks import get_active_library_path
        lib_path = get_active_library_path()
        safe_name = metadata["name"].lower().replace(" ", "_")
        filename = f"{safe_name}.md"
        target_path = f"{lib_path}/skills/{metadata['domain']}/{filename}"

        if os.path.exists(target_path):
            from jcapy.ui.screens.modals.file_exists import FileExistsModal
            def on_confirm(overwrite: bool):
                if overwrite:
                    self._do_harvest(metadata, force=True)
            self.app.push_screen(FileExistsModal(filename), on_confirm)
        else:
            self._do_harvest(metadata)

    def _do_harvest(self, metadata: dict, force: bool = False) -> None:
        """Execute the actual harvest via the engine in a background worker."""
        self.save_skill_worker(metadata, force)
        self.dismiss()

    @work(thread=True)
    def save_skill_worker(self, metadata: dict, force: bool = False) -> None:
        """Background worker for saving the skill using FrameworkEngine."""
        engine = FrameworkEngine()
        result = engine.save_skill(metadata, force=force)

        if result.status == ResultStatus.SUCCESS:
            skill_name = metadata["name"]
            safe_name = result.payload.get("safe_name")
            # Push success screen back on main thread
            self.app.call_from_thread(self.app.push_screen, HarvestSuccessScreen(skill_name, safe_name))
        else:
            self.app.notify(f"Harvest failed: {result.message}", severity="error")

    def action_submit(self) -> None:
        self.submit()

    def action_cancel(self) -> None:
        self.dismiss(None)
