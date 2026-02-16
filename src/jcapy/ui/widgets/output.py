from textual.widgets import Static, RichLog, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from datetime import datetime

class CommandBlock(Vertical):
    """A block displaying command output."""

    DEFAULT_CSS = """
    CommandBlock {
        height: auto;
        max_height: 50;
        margin: 1;
        background: #252526;
        border: solid #3c3c3c;
    }

    .header {
        background: #3c3c3c;
        color: white;
        padding: 0 1;
        height: 1;
        dock: top;
    }

    RichLog {
        height: auto;
        min_height: 5;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1;
    }
    """

    def __init__(self, command: str, output: str, exit_code: int = 0):
        super().__init__()
        self.command = command
        self.output = output
        self.exit_code = exit_code
        self.timestamp = datetime.now().strftime("%H:%M:%S")

    def compose(self) -> ComposeResult:
        status_icon = "✅" if self.exit_code == 0 else "❌"
        header_text = f"{status_icon} {self.timestamp} | {self.command}"

        yield Static(header_text, classes="header")
        log = RichLog(highlight=True, markup=True, id="log")
        yield log

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        if self.output:
            self.add_text(self.output)

    def add_text(self, text: str) -> None:
        """Add text (with ANSI support) to the log."""
        from rich.text import Text
        log = self.query_one("#log", RichLog)
        log.write(Text.from_ansi(text))
