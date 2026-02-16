from datetime import datetime
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal, Grid
from textual.app import ComposeResult
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import os
import subprocess

class ClockWidget(Static):
    """Displays current time (Local/UTC)."""

    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        now = datetime.now()
        utc = datetime.utcnow()
        time_str = f"[bold cyan]{now.strftime('%H:%M:%S')}[/] [dim]LOC[/]  |  [bold yellow]{utc.strftime('%H:%M')}[/] [dim]UTC[/]"
        self.update(Panel(time_str, title="🕒 Time", border_style="blue"))

class WorldMapWidget(Static):
    """Aesthetic World Map."""

    # Simple ASCII Map since complex one might break layout without correct font
    ASCII_MAP = """
       . . . . . . . . . . . . . . . . . . . . .
      . . . . :::::::: . . . . . . . . . . . . .
      . . . :::::::::::: . . . . . . . . . . . .
      . . . :::::::::::: . . .:::::: . . . . . .
      . . . . ::::::::: . . . :::::::: . . . . .
      . . . . . ::::: . . . . ::::::::: . . . . .
      . . . . . . . . . . . . . ::::::::: . . . .
    """

    def compose(self) -> ComposeResult:
        # Align center in the panel
        yield Static(Panel(Align.center(self.ASCII_MAP), title="🌍 Global Operations", border_style="green"))

class ProjectStatusWidget(Static):
    """Current Project Info."""

    def on_mount(self) -> None:
        self.update_status()

    def update_status(self) -> None:
        cwd = os.getcwd()
        project_name = os.path.basename(cwd)

        try:
            # Fix subprocess usage
            branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL).decode().strip()
        except:
            branch = "Not a git repo"

        content = f"""
[bold]Project:[/] {project_name}
[bold]Path:[/]    {cwd}
[bold]Branch:[/]  [magenta]{branch}[/]
        """
        self.update(Panel(content, title="📂 Project Status", border_style="magenta"))

class MarketplaceWidget(Static):
    """Available Skills/Tools."""

    def compose(self) -> ComposeResult:
        # Mock Data for now
        content = """
[green]●[/] Go Microservice
[green]●[/] Python API
[green]●[/] React Frontend
[green]●[/] Terraform AWS
[dim]○[/] Rust CLI (Coming Soon)
        """
        yield Static(Panel(content, title="🛍️  Marketplace", border_style="cyan"))

class MCPWidget(Static):
    """Active MCP Tools."""

    def compose(self) -> ComposeResult:
        content = """
[bold green]Active Servers:[/bold green]
- filesystem
- brave-search
- github

[dim]3 servers connected.[/dim]
        """
        yield Static(Panel(content, title="🔌 MCP Tools", border_style="yellow"))
