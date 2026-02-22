from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.text import Text
import time

class ThinkingHUD(Static):
    """
    A futuristic HUD widget that visualizes the agent's internal reasoning.
    Shows the current 'Thought' and 'Confidence' levels.
    """

    thought = reactive("Initializing cognitive loop...")
    confidence = reactive(0.95)

    DEFAULT_CSS = """
    ThinkingHUD {
        dock: top;
        height: 3;
        background: $surface 10%;
        color: $text 60%;
        border-bottom: solid $accent 10%;
        content-align: center middle;
        text-style: italic;
    }
    """

    def on_mount(self) -> None:
        self.set_interval(5, self.simulate_thinking)

    def simulate_thinking(self) -> None:
        """
        Placeholder for real integration with the agent's thought stream.
        In JCapy 2.0, this would poll the memory/bus for active thoughts.
        """
        thoughts = [
            "Analyzing project structure...",
            "Monitoring file changes...",
            "Heuristic: Dependency conflict detected in pyproject.toml",
            "Cognitive Load: Nominal",
            "Waiting for user input...",
            "Scanning for security vulnerabilities...",
            "Optimizing cognitive context..."
        ]
        import random
        self.thought = random.choice(thoughts)
        self.confidence = random.uniform(0.85, 0.99)

    def watch_thought(self, value: str) -> None:
        self.update_content()

    def update_content(self) -> None:
        content = Text()
        content.append("🧠 ", style="bold magenta")
        content.append(self.thought, style="italic")
        content.append(f"  [ {self.confidence:.2f} ]", style="dim cyan")
        self.update(content)
