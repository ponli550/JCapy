from jcapy.core.base import CommandBase
from jcapy.config import CONFIG_MANAGER
from jcapy.ui.ux.feedback import show_success, show_error
from rich.console import Console

console = Console()

class ThemeCommand(CommandBase):
    name = "theme"
    description = "Switch TUI Theme"

    def setup_parser(self, parser):
        parser.add_argument("name", nargs="?", help="Name of the theme (default, dracula, matrix)", default=None)
        parser.add_argument("--list", action="store_true", help="List available themes")

    def execute(self, args):
        from jcapy.ui.theme import THEMES

        if args.list or not args.name:
            console.print("[bold cyan]Available Themes:[/bold cyan]")
            current_theme = CONFIG_MANAGER.get("ux.theme", "default")
            for name in THEMES.keys():
                marker = " (Active)" if current_theme == name else ""
                console.print(f"  • {name}{marker}")
            return

        if args.name not in THEMES:
            show_error(f"Theme '{args.name}' not found.")
            console.print(f"Available: {', '.join(THEMES.keys())}")
            return

        # Core logic: updating config triggers ConfigUpdated -> App.on_config_updated -> apply_theme
        CONFIG_MANAGER.set("ux.theme", args.name)
        show_success(f"Theme switched to: {args.name}")
