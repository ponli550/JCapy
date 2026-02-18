from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Vertical, Horizontal

class FileExistsModal(ModalScreen[bool]):
    """A modal dialog to confirm file overwrite."""

    DEFAULT_CSS = """
    FileExistsModal {
        align: center middle;
    }

    #dialog {
        padding: 0 1;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
    }

    #message {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        padding: 1;
    }

    Horizontal {
        width: 1fr;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 1 2;
    }
    """

    def __init__(self, filename: str):
        self.filename = filename
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"⚠️  Framework [bold yellow]{self.filename}[/] already exists!", id="message")
            with Horizontal():
                yield Button("Overwrite", variant="error", id="overwrite")
                yield Button("Cancel", variant="primary", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "overwrite":
            self.dismiss(True)
        else:
            self.dismiss(False)
