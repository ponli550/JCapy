from textual.app import App, ComposeResult, AwaitMount
from textual.widgets import Header, Footer, Static, RichLog, Input
from textual.reactive import reactive
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual import work

from jcapy.core.plugins import get_registry, MockArgs
from jcapy.core.service import get_service
from jcapy.core.base import CommandResult, ResultStatus
from jcapy.ui.screens.dashboard import DashboardScreen
from jcapy.ui.screens.management_screen import ManagementScreen
from jcapy.ui.screens.startup import StartupScreen
from jcapy.ui.widgets.palette import CommandPalette
from jcapy.ui.messages import ConfigUpdated
from jcapy.config import CONFIG_MANAGER
from jcapy.ui.menu import terminal_hygiene
from jcapy.ui.screens.prompt import TerminalPromptScreen
from jcapy.ui.modes import InputMode
from jcapy.ui.grammar import GrammarProcessor, Action
import shlex
import time
from typing import Optional, Callable
import logging

logger = logging.getLogger('jcapy.tui')

# ZMQ Bridge integration for Web Control Plane
_zmq_bridge = None

class ModeHUD(Static):
    """A visual indicator for the current input mode and active persona/role."""
    def on_mount(self) -> None:
        self.watch(self.app, "current_mode", self.update_mode)

    def update_mode(self, mode: InputMode) -> None:
        from jcapy.config import CONFIG_MANAGER
        persona = CONFIG_MANAGER.get("current_persona", "N/A")

        # Role logic: Dashboard typically implies Sentinel (Planning),
        # Terminal typically implies Executor (Action).
        role = "SENTINEL" if self.app.screen.id == "dashboard" else "EXECUTOR"
        role_color = "magenta" if role == "SENTINEL" else "cyan"

        color = "cyan"
        if mode == InputMode.INSERT: color = "magenta"
        elif mode == InputMode.VISUAL: color = "yellow"
        elif mode == InputMode.COMMAND: color = "green"

        content = (
            f"[bold {color}][/][bold white on {color}]{mode.name}[/][bold {color}][/]  "
            f"[dim]Role:[/] [bold {role_color}]{role}[/] [dim] • [/] "
            f"[dim]Persona:[/] [bold cyan]{persona.capitalize()}[/]"
        )
        self.update(content)
class JCapyApp(App):
    """JCapy: The Knowledge Operating System"""

    current_mode = reactive(InputMode.NORMAL)

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

    # Dynamically handled keys (Intercepted in on_key)
    # i -> switch_mode('insert')
    # v -> switch_mode('visual')
    # esc -> switch_mode('normal')

    SCREENS = {
        "dashboard": DashboardScreen,
        "management": ManagementScreen,
        "startup": StartupScreen,
    }

    def __init__(self, start_screen: str = "dashboard", **kwargs):
        self.start_screen = start_screen
        self.grammar = GrammarProcessor()
        self.is_orbital = False
        self.client = None
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
        header = Header(show_clock=True)
        header.tall = True
        yield header
        yield ModeHUD(id="mode-hud")
        with Container(id="main-container"):
            with Horizontal(id="terminal-container"):
                # Left Pane: Main Output
                with Vertical(id="output-pane"):
                    yield Static("TERMINAL OUTPUT", classes="pane-label")
                    yield RichLog(id="terminal-log", highlight=True, markup=True, wrap=True)

                # Right Pane: Command Center
                with Vertical(id="input-pane"):
                    yield Static("COMMAND CENTER", classes="pane-label")
                    yield Static("[bold cyan]Command History[/]", classes="pane-header")
                    yield RichLog(id="history-log", highlight=True, markup=True)
                    yield Input(placeholder="❯ Enter command...", id="term-input")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Bind config manager for reactive updates
        from jcapy.config import CONFIG_MANAGER, get_ux_preference
        CONFIG_MANAGER.bind_app(self)

        # Apply persistent theme
        theme = get_ux_preference("theme")
        self.apply_theme(theme)

        # Initialize ZMQ bridge for Web Control Plane communication
        self._init_zmq_bridge()

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

        # Auto-focus the terminal input
        self.query_one("#term-input").focus()

    def _init_zmq_bridge(self) -> None:
        """Initialize ZMQ bridge for TUI ↔ Web communication."""
        global _zmq_bridge
        try:
            from jcapy.core.zmq_publisher import init_zmq_bridge, start_zmq_bridge
            from jcapy.core.bus import get_event_bus, attach_zmq_to_bus

            # Check if bridge already exists (e.g., from daemon)
            from jcapy.core.zmq_publisher import get_zmq_bridge
            _zmq_bridge = get_zmq_bridge()

            if _zmq_bridge and _zmq_bridge.is_running:
                logger.info("ZMQ bridge already running (from daemon)")
                attach_zmq_to_bus()
            else:
                # Create new bridge
                _zmq_bridge = init_zmq_bridge(
                    pub_port=5555,
                    rpc_port=5556,
                    command_handler=self._handle_web_command
                )

                if start_zmq_bridge():
                    logger.info("✅ TUI ZMQ Bridge started")
                    attach_zmq_to_bus()
                else:
                    logger.warning("⚠️ TUI ZMQ Bridge failed to start")

        except ImportError as e:
            logger.warning(f"⚠️ ZMQ not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize ZMQ bridge: {e}")

    def _handle_web_command(self, command: str, params: dict) -> dict:
        """Handle commands received from Web Control Plane."""
        logger.info(f"Received Web command: {command}")

        if command == "EXECUTE_COMMAND":
            cmd_str = params.get("command", "")
            if cmd_str:
                # Execute in TUI
                self.call_from_thread(self.run_command, cmd_str)
                return {"status": "executed", "command": cmd_str}
            return {"status": "error", "message": "No command provided"}

        elif command == "SWITCH_PERSONA":
            persona = params.get("persona", "")
            if persona:
                self.call_from_thread(self.run_command, f"persona activate {persona}")
                return {"status": "ok", "persona": persona}
            return {"status": "error", "message": "No persona specified"}

        elif command == "GET_STATUS":
            return {
                "status": "ok",
                "mode": self.current_mode.name,
                "persona": CONFIG_MANAGER.get("current_persona", "N/A")
            }

        else:
            return {"status": "error", "message": f"Unknown command: {command}"}

    def on_unmount(self) -> None:
        """Called when app shuts down."""
        global _zmq_bridge
        if _zmq_bridge:
            try:
                _zmq_bridge.stop()
                logger.info("ZMQ bridge stopped")
            except Exception as e:
                logger.error(f"Error stopping ZMQ bridge: {e}")

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

    def on_descendant_focus(self, event) -> None:
        """Switch to INSERT mode automatically when an Input gains focus."""
        if isinstance(event.widget, Input):
            self.current_mode = InputMode.INSERT

    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme by injecting CSS variables."""
        from jcapy.ui.theme import THEMES
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
    # Modal & Cursor Management
    # ------------------------------------------------------------------

    def watch_current_mode(self, mode: InputMode) -> None:
        """Update the terminal cursor shape when the mode changes."""
        self.set_terminal_cursor_shape(mode)
        # self.notify(f"Mode: [bold cyan]{mode.name}[/]", severity="information", timeout=2)

    def set_terminal_cursor_shape(self, mode: InputMode) -> None:
        """Emit ANSI DECSUSR sequences to set the terminal cursor shape."""
        import sys
        try:
            if mode == InputMode.INSERT:
                sys.stdout.write("\x1b[6 q")  # Vertical bar (I-beam)
            elif mode == InputMode.VISUAL:
                sys.stdout.write("\x1b[4 q")  # Underline
            else:
                sys.stdout.write("\x1b[2 q")  # Block (default)
            sys.stdout.flush()
        except Exception:
            pass  # Fail gracefully if stdout is not a TTY or pipe

    def action_switch_mode(self, mode_name: str) -> None:
        """Switch the current input mode."""
        try:
            self.current_mode = InputMode[mode_name.upper()]
        except KeyError:
            pass

    def on_key(self, event) -> None:
        """Global key interceptor for modal logic."""
        # 0. Bypass modality if a modal screen is active
        if isinstance(self.screen, ModalScreen):
            return

        key = event.key

        # 1. ESC always returns to NORMAL mode
        if key == "escape":
            if self.current_mode != InputMode.NORMAL:
                self.current_mode = InputMode.NORMAL
                if self.focused:
                    self.focused.blur()
                event.stop()
                return

        # 2. Logic depends on mode
        if self.current_mode == InputMode.NORMAL:
            # 2.1 Grammar Processing
            action = self.grammar.process_key(key)
            if action:
                self.execute_grammar_action(action)
                event.stop()
                return
            elif self.grammar.partial_verb:
                # We are in the middle of a sequence, don't let other handlers trigger
                event.stop()
                return

            # Handle modal transitions
            if key == "i":
                self.action_switch_mode("insert")
                # Auto-focus input if on main terminal
                try:
                    self.query_one("#term-input").focus()
                except: pass
                event.stop()
            elif key == "v":
                self.action_switch_mode("visual")
                event.stop()
            elif key == ":":
                self.action_toggle_command_mode()
                event.stop()
            # Navigation h/j/k/l (already handle j/k via bindings, but let's be explicit)
            elif key in ("h", "l"):
                 # Handle horizontal movement if relevant
                 pass

        elif self.current_mode == InputMode.INSERT:
            # In INSERT mode, we let almost everything pass to focused widget.
            if key == "ctrl+c": # Core exit
                return
            pass

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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission from the persistent input."""
        if event.input.id == "term-input":
            command = event.value.strip()
            if command:
                self._log_command_to_history(command)
                self.run_command(command)
                event.input.value = ""

    def _log_command_to_history(self, command: str) -> None:
        """Centralized logging for command history across all inputs."""
        # 1. Main Terminal History
        try:
            history = self.query_one("#history-log", RichLog)
            history.write(f"[dim]❯[/] {command}")
        except: pass

        # 2. Console Drawer Log (if visible)
        try:
            drawer = self.screen.query_one("#dashboard-console")
            drawer.write(f"\n[bold green]❯ {command}[/]")
        except: pass

    # ------------------------------------------------------------------
    # Shared Engine: Command Execution
    # ------------------------------------------------------------------

    @work(thread=True, exit_on_error=False)
    def run_command(self, command_str: str, tui_data: Optional[dict] = None, on_complete: Optional[Callable] = None) -> None:
        """Execute a command via the Shared Engine and route the result."""
        # --- Shell Suspension ---
        cmd_clean = command_str.strip().split(" ")[0].lower()

        # 0. Check if command is interactive → suspend TUI and run directly
        registry = get_registry()
        canonical = registry._aliases.get(cmd_clean, cmd_clean)

        # 0. Check for Internal TUI Routing
        # Use screens/modals instead of suspending the TTY.
        if canonical == "harvest" and not tui_data:
            from jcapy.ui.screens.harvest import HarvestScreen
            def on_harvest_result(result):
                if result:
                     self.run_command("harvest", tui_data=result)
            self.call_from_thread(self.push_screen, HarvestScreen(), on_harvest_result)
            return

        if canonical == "init" and not tui_data:
            def on_init_grade(grade):
                if grade:
                     self.run_command("init", tui_data={"grade": grade})
            self.call_from_thread(self.push_screen, TerminalPromptScreen(
                prompt="Select Project Grade",
                choices=["A (Fortress)", "B (Campaign)", "C (Skirmish)"],
                default="B"
            ), on_init_grade)
            return

        if canonical == "deploy" and not tui_data:
            def on_deploy_choice(choice):
                if choice:
                     try:
                         idx = int(choice.split(")")[0].strip()) - 1
                         self.run_command("deploy", tui_data={"choice_idx": idx})
                     except:
                         self.run_command("deploy", tui_data={"choice_idx": 0})

            self.call_from_thread(self.push_screen, TerminalPromptScreen(
                prompt="Select Deployment Strategy",
                choices=["1) Standard (Detected)", "2) Custom (Manual Command)"],
                default="1"
            ), on_deploy_choice)
            return

        if canonical == "brainstorm" and not tui_data:
            from jcapy.ui.screens.brainstorm_screen import BrainstormScreen
            def on_brainstorm_result(res):
                if res:
                    file, provider = res
                    # Execute non-interactively
                    self.run_command(f"brainstorm {file} --provider {provider}", tui_data={"routed": True})
            self.call_from_thread(self.push_screen, BrainstormScreen(), on_brainstorm_result)
            return

        if canonical == "persona":
            parts = shlex.split(command_str)
            if len(parts) == 1:
                # persona (no args) -> Route to management screen
                self.call_from_thread(self.switch_screen, "management")
                return

        if canonical in ("manage", "tui"):
            screen = "management" if canonical == "manage" else "dashboard"
            self.call_from_thread(self.switch_screen, screen)
            return

        # Catch-all for other interactive commands that aren't natively routed yet
        if canonical in registry._interactive:
            # If no flags are provided, warn the user
            parts = shlex.split(command_str)
            if len(parts) == 1:
                self.notify(f"'{canonical}' is interactive. Use flags (e.g. --yes) for best results in TUI.", severity="warning")

        if cmd_clean in ("shell", "suspend"):
            self.notify("Shell suspension is not supported in the unified TUI terminal.", severity="warning")
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

        if self.is_orbital and self.client:
            # Delegate to Daemon via gRPC
            response = self.client.execute(command_str, context=tui_data)
            # Map gRPC Response to CommandResult
            result = CommandResult(
                status=ResultStatus.SUCCESS if response.status == "success" else ResultStatus.FAILURE,
                message=response.message,
                data=json.loads(response.result_data_json) if response.result_data_json else {}
            )
        else:
            # Local Execution
            service = get_service()
            result: CommandResult = service.execute(command_str, log_callback=streaming_callback, tui_data=tui_data)

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

        # 4. Trigger completion callback
        if on_complete:
            self.call_from_thread(on_complete, result)

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

    def execute_grammar_action(self, action: Action) -> None:
        """Execute a completed grammar sequence on the focused widget."""
        from textual.widgets import Input, TextArea

        target = self.focused
        if not target:
            return

        summary = f"{action.verb} {action.noun}"
        if action.count > 1: summary += f" x{action.count}"
        self.notify(f"󰄬 Grammar: [bold cyan]{summary}[/]", severity="information", timeout=2)

        # Implementation of basic actions
        if action.verb == "delete":
            if action.noun == "line":
                if isinstance(target, Input):
                    target.value = ""
                elif isinstance(target, TextArea):
                    # Simple line deletion for TextArea
                    cursor = target.cursor_location
                    lines = target.text.splitlines()
                    if 0 <= cursor[0] < len(lines):
                        lines.pop(cursor[0])
                        target.text = "\n".join(lines)
            elif action.noun == "word":
                if isinstance(target, Input):
                    # Basic word deletion (forward)
                    val = target.value
                    pos = target.cursor_position
                    import re
                    match = re.search(r'\w+\s*', val[pos:])
                    if match:
                        target.value = val[:pos] + val[pos + match.end():]

        elif action.verb == "change":
            if action.noun == "line":
                 if isinstance(target, Input):
                     target.value = ""
                     self.action_switch_mode("insert")
            elif action.noun == "word":
                 if isinstance(target, Input):
                      # Delete word and go to insert
                      val = target.value
                      pos = target.cursor_position
                      import re
                      match = re.search(r'\w+\s*', val[pos:])
                      if match:
                          target.value = val[:pos] + val[pos + match.end():]
                          self.action_switch_mode("insert")

        elif action.verb == "paste":
             # Placeholder for clipboard integration
             self.notify("Paste not yet implemented in Terminal core", severity="warning")


if __name__ == "__main__":
    app = JCapyApp()
    app.run()

