from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog
from textual.containers import Container, VerticalScroll
from textual import work

from jcapy.core.plugins import get_registry
from jcapy.core.base import CommandResult, ResultStatus
from jcapy.ui.screens.dashboard import DashboardScreen
from jcapy.ui.widgets.palette import CommandPalette


class JCapyApp(App):
    """JCapy: The Knowledge Operating System"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+p", "toggle_palette", "Command Palette"),
        ("ctrl+c", "quit", "Quit"),
        ("d", "dashboard", "Dashboard"),
        ("q", "quit", "Quit"),
        ("/", "toggle_palette", "Search"),
        (":", "toggle_command_mode", "Command Mode"),
        ("j", "scroll_down", "Scroll Down"),
        ("k", "scroll_up", "Scroll Up"),
        ("`", "toggle_console", "Toggle Console"),
    ]

    SCREENS = {"dashboard": DashboardScreen}

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with VerticalScroll(id="terminal-scroll"):
                yield RichLog(id="terminal-log", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Write welcome message so terminal view isn't blank
        log = self.query_one("#terminal-log", RichLog)
        log.write("[bold cyan]JCapy Terminal[/bold cyan]  [dim]Press Ctrl+P or : to run commands[/dim]\n")
        self.push_screen("dashboard")

    # ------------------------------------------------------------------
    # Command Palette Actions
    # ------------------------------------------------------------------

    def action_toggle_palette(self) -> None:
        """Toggle Command Palette."""
        def handle_command(command_str: str | None) -> None:
            if command_str:
                self.run_command(command_str)
        self.push_screen(CommandPalette(), handle_command)

    def action_toggle_command_mode(self) -> None:
        """Enter command mode (prefills :)."""
        def handle_command(command_str: str | None) -> None:
            if command_str:
                self.run_command(command_str)
        self.push_screen(CommandPalette(), handle_command)

    def action_dashboard(self) -> None:
        """Return to dashboard."""
        self.push_screen("dashboard")

    # ------------------------------------------------------------------
    # Shared Engine: Command Execution
    # ------------------------------------------------------------------

    @work(thread=True, exit_on_error=False)
    def run_command(self, command_str: str) -> None:
        """Execute a command via the Shared Engine and route the result."""
        # --- Shell Suspension ---
        cmd_clean = command_str.strip().lower()
        if cmd_clean in ("shell", "suspend"):
            with self.suspend():
                import subprocess
                import os
                subprocess.run([os.environ.get("SHELL", "zsh")])
            return

        # Ensure we're on the terminal view
        if isinstance(self.screen, DashboardScreen):
            self.call_from_thread(self.pop_screen)

        # Show immediate feedback (fix for "stuck" perception)
        self.call_from_thread(self._render_command_start, command_str)

        registry = get_registry()
        result: CommandResult = registry.execute_string(command_str)

        # Render output to the terminal log
        self.call_from_thread(self._render_result, command_str, result)

        # Route UI hints
        if result.ui_hint:
            self.call_from_thread(self._handle_ui_hint, result)

        # Toast notification (unless silent)
        if not result.silent and result.message:
            severity = "information"
            if result.status == ResultStatus.FAILURE:
                severity = "error"
            elif result.status == ResultStatus.WARNING:
                severity = "warning"
            self.call_from_thread(self.notify, result.message, severity=severity)

    # ------------------------------------------------------------------
    # Rendering Helpers
    # ------------------------------------------------------------------

    def _render_command_start(self, command_str: str) -> None:
        """Show a loading indicator."""
        log = self.query_one("#terminal-log", RichLog)
        log.write(f"\n[dim]⏳ Running '{command_str}'...[/dim]")

    def _render_result(self, command_str: str, result: CommandResult) -> None:
        """Write a CommandResult into the terminal RichLog."""
        log = self.query_one("#terminal-log", RichLog)

        # Route to Dashboard Console Drawer if present
        try:
            drawer = self.screen.query_one("#dashboard-console")
            drawer.write(f"\n[bold green]❯ {command_str}[/]")
            for entry in result.logs:
                if entry.strip():
                    drawer.write(entry)
        except:
            pass

        # Command header
        status_icon = "✔" if result.status == ResultStatus.SUCCESS else "✘"
        color = "green" if result.status == ResultStatus.SUCCESS else "red"
        log.write(f"\n[bold {color}]{status_icon}[/bold {color}] [bold]> {command_str}[/bold]  [dim]{result.duration:.2f}s[/dim]")

        # Logs (captured stdout / structured logs)
        for entry in result.logs:
            if entry.strip():
                log.write(entry)

        # Modern: Render structured content (e.g. Markdown reports)
        if result.data and isinstance(result.data, dict) and "content" in result.data:
            from rich.markdown import Markdown
            log.write(Markdown(result.data["content"]))

        # Message summary
        if result.message and result.status == ResultStatus.FAILURE:
            log.write(f"[bold red]  ⚠ {result.message}[/bold red]")

    def _handle_ui_hint(self, result: CommandResult) -> None:
        """Route a ui_hint to the appropriate widget or screen."""
        hint = result.ui_hint

        if hint == "refresh_tree":
            try:
                self.query_one("#project-tree").reload_data(result.data)
            except Exception:
                pass  # Widget may not be mounted

        elif hint.startswith("open_screen:"):
            screen_name = hint.split(":")[1]
            try:
                self.push_screen(screen_name)
            except Exception:
                pass

        elif hint.startswith("open_file:"):
            # For now, just notify. Later: Open in internal viewer or system editor?
            file_path = hint.split(":")[1]
            self.notify(f"Report saved to: {file_path}", title="File Saved", severity="information")

        elif hint == "notify":
            self.notify(result.message, severity=result.status.value)

    def action_toggle_console(self) -> None:
        """Toggle the slide-up console drawer."""
        try:
            drawer = self.screen.query_one("#dashboard-console")
            drawer.toggle()
        except:
            pass

    # ------------------------------------------------------------------
    # Navigation Helpers
    # ------------------------------------------------------------------

    def action_scroll_down(self) -> None:
        """Scroll active container down."""
        if not isinstance(self.screen, DashboardScreen):
            try:
                self.query_one("#terminal-scroll").scroll_down(animate=False)
            except Exception:
                pass

    def action_scroll_up(self) -> None:
        """Scroll active container up."""
        if not isinstance(self.screen, DashboardScreen):
            try:
                self.query_one("#terminal-scroll").scroll_up(animate=False)
            except Exception:
                pass


if __name__ == "__main__":
    app = JCapyApp()
    app.run()

