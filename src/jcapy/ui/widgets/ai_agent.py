from textual.widget import Widget
from textual.widgets import Static, Label, ProgressBar
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from rich.panel import Panel
from rich.text import Text

class AIAgentWidget(Widget):
    """
    Visualizes AI Agent thoughts, confidence, and active subagents.
    Acts as the 'pulse' of the system.
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="ai-agent-root"):
            yield Label("🧠 AI ORCHESTRATOR", classes="col-header")

            with Vertical(classes="ai-card"):
                yield Label("[dim]CURRENT THOUGHT[/dim]", classes="ai-label")
                yield Label("[cyan]❯ Analyzing repository architecture...[/]", id="ai-thought-text")

            with Vertical(classes="ai-card"):
                yield Label("[dim]CONFIDENCE SCORE[/dim]", classes="ai-label")
                yield ProgressBar(total=100, show_bar=True, show_percentage=True, id="ai-confidence")

            with Vertical(classes="ai-card"):
                yield Label("[dim]ACTIVE SUBAGENTS[/dim]", classes="ai-label")
                yield Static("󰚩 [bold green]Architect[/] [dim](Primary)[/]\n󰛦 [bold yellow]Research [dim](Idle)[/]", id="ai-subagents")

    def on_mount(self) -> None:
        self.update_pulse("Refining widget visual hierarchy...", 85)

    def update_pulse(self, thought: str, confidence: int) -> None:
        """Update the widget state with new data."""
        try:
            self.query_one("#ai-thought-text").update(f"[cyan]❯ {thought}[/]")
            self.query_one("#ai-confidence").update(progress=confidence)
        except:
            pass
