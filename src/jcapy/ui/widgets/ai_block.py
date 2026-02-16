from textual.widgets import Static, RichLog
from textual.containers import Vertical
from textual.app import ComposeResult
from datetime import datetime

class AIBlock(Vertical):
    """A block displaying AI interaction/thinking."""

    DEFAULT_CSS = """
    AIBlock {
        height: auto;
        max_height: 60;
        margin: 1;
        background: #1e1e1e;
        border: dashed #007acc;
    }

    .ai-header {
        background: #007acc;
        color: white;
        padding: 0 1;
        height: 1;
        dock: top;
        text-align: right;
    }

    RichLog {
        height: auto;
        min_height: 5;
        background: #1e1e1e;
        color: #cecece;
        padding: 1;
    }
    """

    def __init__(self, topic: str, content: str):
        super().__init__()
        self.topic = topic
        self.content = content
        self.timestamp = datetime.now().strftime("%H:%M:%S")

    def compose(self) -> ComposeResult:
        header_text = f"🤖 AI Assistant | {self.timestamp}"
        yield Static(header_text, classes="ai-header")
        log = RichLog(highlight=True, markup=True)
        log.write(f"[bold cyan]Topic:[/bold cyan] {self.topic}\n")
        log.write(self.content)
        yield log
