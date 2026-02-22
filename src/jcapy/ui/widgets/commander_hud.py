from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.text import Text
import subprocess
import os
import time

class CommanderHUD(Static):
    """
    The Mission Control header for JCapy.
    Combines AI Thinking telemetry with real-time environment health (Git, Personas).
    """

    thought = reactive("Initializing Mission Control...")
    git_status = reactive("Checking Git...")
    persona_health = reactive("Personas: OK")
    guardrails = reactive("🛡️ [green]GUARDRAILS: NOMINAL[/]")

    DEFAULT_CSS = """
    CommanderHUD {
        dock: top;
        height: 4;
        background: $surface 15%;
        color: $text 80%;
        border-bottom: double $accent;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self.set_interval(10, self.refresh_environment)
        self.set_interval(5, self.simulate_thinking)
        self.set_interval(15, self.check_guardrails)

    def refresh_environment(self) -> None:
        """Check Git remotes and persona directories."""
        # 1. Check Git Remote
        try:
            remote = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            self.git_status = f"🛰️ [dim]Remote:[/] [cyan]{remote.split('/')[-1]}[/]"
        except:
            self.git_status = "🛰️ [bold red]LOCAL ONLY[/]"

        # 2. Check Personas (Heuristic: are they present and initialized?)
        # For now, a simple check of common paths
        if os.path.exists(".agents") or os.path.exists("jcapy-skills"):
            self.persona_health = "👤 [green]Personas: ACTIVE[/]"
        else:
            self.persona_health = "👤 [yellow]Personas: MISSING[/]"

    def check_guardrails(self) -> None:
        """Heuristic check for One-Army standards."""
        issues = []
        if not os.path.exists(".gemini/antigravity/brain/task.md"):
            issues.append("MISSING TASK.MD")

        try:
            status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True).strip()
            if status:
                issues.append("UNCOMMITTED CHANGES")
        except:
            pass

        if issues:
            self.guardrails = f"🛡️ [bold yellow]GUARDRAILS: {', '.join(issues)}[/]"
        else:
            self.guardrails = "🛡️ [green]GUARDRAILS: NOMINAL[/]"

    def simulate_thinking(self) -> None:
        """Simulate autonomous thought stream."""
        thoughts = [
            "Auditing security guardrails...",
            "Monitoring One-Army resource allocation...",
            "Strategy: Transitioning to Governance Mode",
            "Cognitive Entropy: 0.04",
            "Synthesizing infrastructure health...",
            "Awaiting command deployment..."
        ]
        import random
        self.thought = random.choice(thoughts)

    def render(self) -> Text:
        content = Text()
        content.append("\n")
        # Line 1: Strategic Status
        content.append("🧠 ", style="bold magenta")
        content.append(self.thought.ljust(50), style="italic")
        content.append(" | ", style="dim")
        content.append(self.persona_health)

        content.append("\n")
        # Line 2: Infrastructure Health
        content.append("🛰️ ", style="bold blue")
        git_text = Text.from_markup(self.git_status)
        git_text.set_length(50)
        content.append(git_text)
        content.append(" | ", style="dim")
        content.append(Text.from_markup(self.guardrails))

        return content
