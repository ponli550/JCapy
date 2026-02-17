from textual.app import App, ComposeResult, AwaitMount
from textual.widgets import Header, Footer, Static, RichLog
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual import work

from jcapy.core.plugins import get_registry, MockArgs
from jcapy.core.base import CommandResult, ResultStatus
from jcapy.ui.screens.dashboard import DashboardScreen
from jcapy.ui.screens.management_screen import ManagementScreen
from jcapy.ui.screens.startup import StartupScreen
from jcapy.ui.widgets.palette import CommandPalette
from jcapy.ui.messages import ConfigUpdated
from jcapy.config import CONFIG_MANAGER
from jcapy.ui.theme import THEMES
import shlex


class JCapyApp(App):
    """JCapy: The Knowledge Operating System"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+p", "toggle_palette", "Command Palette"),
        ("ctrl+c", "quit", "Quit"),
        ("d", "switch_screen('dashboard')", "Dashboard"),
        ("m", "switch_screen('management')", "Manage"),
        ("q", "quit", "Quit"),
        ("/", "toggle_palette", "Search"),
        (":", "toggle_command_mode", "Command Mode"),
        ("j", "scroll_down", "Scroll Down"),
        ("k", "scroll_up", "Scroll Up"),
        ("`", "toggle_console", "Toggle Console"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "management": ManagementScreen,
        "startup": StartupScreen,
    }

    def __init__(self, start_screen: str = "dashboard", **kwargs):
        self.start_screen = start_screen
        super().__init__(**kwargs)

    def switch_screen(self, screen: str | Screen) -> AwaitMount:
        """
        Override switch_screen to prevent crash when stack is empty.
        If we are on the root/default screen, we push instead of switch.
        """
        if len(self._screen_stack) <= 1:
             return self.push_screen(screen)
        return super().switch_screen(screen)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with VerticalScroll(id="terminal-scroll"):
                yield RichLog(id="terminal-log", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Bind config manager for reactive updates
        from jcapy.config import CONFIG_MANAGER
        CONFIG_MANAGER.bind_app(self)

        # Write welcome message so terminal view isn't blank
        log = self.query_one("#terminal-log", RichLog)
        log.write("[bold cyan]JCapy Terminal[/bold cyan]  [dim]Press Ctrl+P or : to run commands[/dim]\n")

        # Apply startup animation (unless reduced motion)
        from jcapy.ui.animations import should_animate
        target = self.start_screen if self.start_screen in self.SCREENS else "dashboard"

        if should_animate():
             # Push Startup with a clear landing target
             self.push_screen(StartupScreen(next_screen=target))
        else:
             # Fast-path: go straight to target
             self.push_screen(target)

    def on_config_updated(self, message: ConfigUpdated) -> None:
        """Handle configuration updates."""
        if message.key == "ux.theme" or message.key == "*":
            self.apply_theme(message.value)
            self.notify(f"Theme changed to: {message.value}")

        if message.key == "core.persona":
            self.notify(f"Switching persona to: {message.value}")
            # Persona application logic is handled by the command/config logic mostly,
            # but we might need to trigger visual refreshes if persona implies theme/layout changes.
            # The apply_persona function ALREADY updates config keys for dashboard_layout and theme.
            # So those specific ConfigUpdated events will fire separately and be handled.
            pass

        if message.key == "commands.disabled":
            get_registry().apply_disabled_from_config()
            self.notify("Enabled/Disabled commands updated.")
            # Refresh command palette if open?
            # It re-queries registry on open, so just closing/opening is enough.

    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme by injecting CSS variables."""
        theme = THEMES.get(theme_name, THEMES["default"])

        # Try to set variables directly if supported (Textual 0.38+)
        if hasattr(self.stylesheet, "set_variables"):
            try:
                self.stylesheet.set_variables(theme)
                self.refresh_css()
                return
            except Exception:
                pass

        # Fallback: Ingest variables as CSS rules
        css_rules = ["Screen {"]
        for key, value in theme.items():
            css_rules.append(f"    ${key}: {value};")
        css_rules.append("}")
        self.stylesheet.add_source("\n".join(css_rules))
        self.refresh_css()

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
        cmd_clean = command_str.strip().split(" ")[0].lower()

        # 0. Check if command is interactive → suspend TUI and run directly
        registry = get_registry()
        canonical = registry._aliases.get(cmd_clean, cmd_clean)

        if canonical in registry._interactive:
            handler = registry.get_handler(cmd_clean)
            if handler:
                parts = shlex.split(command_str)
                mock_args = MockArgs(parts[1:])
                with self.suspend():
                    try:
                        handler(mock_args)  # Run with mock args
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                    input("\nPress Enter to return to JCapy Dashboard...")
                return

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

        log = self.query_one("#terminal-log", RichLog)

        def streaming_callback(val: str):
            # Route to main log
            self.call_from_thread(log.write, self._ansi_to_text(val))
            # Route to Dashboard Console Drawer if present
            try:
                drawer = self.screen.query_one("#dashboard-console")
                self.call_from_thread(drawer.write, self._ansi_to_text(val))
            except:
                pass

        registry = get_registry()
        result: CommandResult = registry.execute_string(command_str, log_callback=streaming_callback)

        # --- Shell Fallback ---
        if result.status == ResultStatus.FAILURE and result.error_code == "UNKNOWN_COMMAND":
            import subprocess
            try:
                # Fallback to system shell for unknown commands
                process = subprocess.Popen(
                    command_str,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Reset duration start for shell command
                shell_start = time.time()

                # Stream output
                if process.stdout:
                    for line in process.stdout:
                        streaming_callback(line)

                process.wait()
                elapsed = time.time() - shell_start

                result = CommandResult(
                    status=ResultStatus.SUCCESS if process.returncode == 0 else ResultStatus.FAILURE,
                    message=f"System command '{cmd_clean}' completed." if process.returncode == 0 else f"System command '{cmd_clean}' failed.",
                    duration=elapsed
                )
            except Exception as e:
                result = CommandResult(
                    status=ResultStatus.FAILURE,
                    message=f"Shell error: {str(e)}",
                    error_code="SHELL_ERROR"
                )

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

    @staticmethod
    def _ansi_to_text(entry: str):
        """Convert an ANSI-encoded string to a Rich Text object for RichLog.

        Captured stdout from commands using Rich Console contains raw ANSI
        escape codes (e.g. \\x1b[36m).  RichLog.write() with markup=True
        cannot parse these — it expects Rich markup like [bold cyan].
        Text.from_ansi() handles the conversion correctly.
        """
        from rich.text import Text
        return Text.from_ansi(entry.rstrip("\n"))

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
                    drawer.write(self._ansi_to_text(entry))
        except:
            pass

        # Command header
        status_icon = "✔" if result.status == ResultStatus.SUCCESS else "✘"
        color = "green" if result.status == ResultStatus.SUCCESS else "red"
        log.write(f"\n[bold {color}]{status_icon}[/bold {color}] [bold]> {command_str}[/bold]  [dim]{result.duration:.2f}s[/dim]")

        # Logs are now streamed in real-time via the callback in run_command.
        # We skip rendering result.logs here to avoid duplicates, unless it's a legacy non-TUI path.
        # (captured stdout / structured logs) — convert ANSI to Rich Text
        # for entry in result.logs:
        #     if entry.strip():
        #         log.write(self._ansi_to_text(entry))

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

