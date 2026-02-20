# SPDX-License-Identifier: Apache-2.0
import contextlib
import importlib.metadata
import importlib.util
import io
import os
import shlex
import sys
import time
import yaml
from typing import Dict, Any, Callable, Optional, List

from jcapy.core.base import CommandResult, ResultStatus
from jcapy.core.history import HISTORY_MANAGER


class MockArgs:
    """Lightweight namespace for passing arguments to legacy handlers."""
    def __init__(self, tokens: list, piped_data: Optional[str] = None, tui_data: Optional[dict] = None):
        self._tokens = tokens
        self.piped_data = piped_data
        self.tui_data = tui_data

    def __getattr__(self, item):
        return None

class StreamingIO(io.StringIO):
    """Overrides write() to trigger a callback for real-time streaming."""
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.callback = callback

    def write(self, s: str) -> int:
        if self.callback:
            self.callback(s)
        return super().write(s)


class CommandRegistry:
    """
    Central registry for JCapy commands.
    Allows plugins to register new commands dynamically.
    """
    def __init__(self):
        self._commands: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
        self._aliases: Dict[str, str] = {}
        self._arguments: Dict[str, Callable] = {} # Hook for argparse setup
        self._interactive: set = set()  # Commands that need raw TTY (can't run in TUI)
        self._disabled: set = set()     # Commands hidden from execution by config

    def register(self, name, handler: Callable = None, description: str = None, aliases: List[str] = None, setup_parser: Callable = None, interactive: bool = False):
        """
        Register a new command.
        Supports both function-based and class-based (CommandBase) registration.

        Args:
            name: Command name OR CommandBase instance
            handler: Function to call (if name provided)
            description: Help text (if name provided)
            aliases: List of alias names (if name provided)
            setup_parser: Function taking (parser) to add arguments (if name provided)
        """
        if hasattr(name, 'name') and hasattr(name, 'execute'):
             # Class-based registration
             cmd = name
             name = cmd.name
             handler = cmd.execute
             description = getattr(cmd, 'description', "")
             aliases = getattr(cmd, 'aliases', [])
             setup_parser = cmd.setup_parser
             interactive = getattr(cmd, 'is_interactive', False) or interactive

        self._commands[name] = handler
        self._descriptions[name] = description
        self._arguments[name] = setup_parser

        if interactive:
            self._interactive.add(name)

        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

    def get_interactive_defaults(self) -> set:
        """Return the hardcoded interactive command set (for config reset)."""
        return self._interactive.copy()

    def apply_config_overrides(self):
        """
        Read `commands.interactive` from ConfigManager and override the
        _interactive set. Format: comma-separated command names.

        Usage:
            jcapy config set commands.interactive "init,deploy,harvest,persona,tutorial"
            jcapy config get commands.interactive
        """
        try:
            from jcapy.config import CONFIG_MANAGER
            override = CONFIG_MANAGER.get("commands.interactive")
            if override and isinstance(override, str):
                names = [n.strip() for n in override.split(",") if n.strip()]
                # Validate: only allow known commands
                valid = {n for n in names if n in self._commands}
                invalid = set(names) - valid
                if invalid:
                    import sys
                    print(f"[jcapy] Warning: unknown interactive commands ignored: {invalid}", file=sys.stderr)
                self._interactive = valid
        except Exception:
            pass  # Config not available yet — use hardcoded defaults

    def disable_command(self, name: str):
        """Disable a command (hide from palette & block execution)."""
        canonical = self._aliases.get(name, name)
        if canonical in self._commands:
            self._disabled.add(canonical)

    def enable_command(self, name: str):
        """Re-enable a previously disabled command."""
        canonical = self._aliases.get(name, name)
        self._disabled.discard(canonical)

    def apply_disabled_from_config(self):
        """Read `commands.disabled` from ConfigManager."""
        try:
            from jcapy.config import CONFIG_MANAGER
            val = CONFIG_MANAGER.get("commands.disabled", "")
            if val and isinstance(val, str):
                names = [n.strip() for n in val.split(",") if n.strip()]
                # Verify commands exist before disabling
                self._disabled = {n for n in names if n in self._commands}
            else:
                self._disabled = set()
        except Exception:
            pass

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get the handler for a command, resolving aliases."""
        if name in self._commands:
            return self._commands[name]

        if name in self._aliases:
            real_name = self._aliases[name]
            return self._commands.get(real_name)

        return None

    def get_commands(self) -> Dict[str, str]:
        """Return all registered commands and descriptions (excluding disabled)."""
        return {k: v for k, v in self._descriptions.items() if k not in self._disabled}

    # ------------------------------------------------------------------
    # Shared Engine: Unified Dispatcher (CLI + TUI)
    # ------------------------------------------------------------------

    def execute_string(self, command_str: str, log_callback: Optional[Callable[[str], None]] = None, tui_data: Optional[dict] = None) -> CommandResult:
        """
        Parse a raw command string and execute it via the registry.
        Supports integrated piping via '|'.
        """
        # Save to history
        HISTORY_MANAGER.add_command(command_str)

        # Handle Piping
        if "|" in command_str:
            stages = [s.strip() for s in command_str.split("|")]
            last_result = None
            piped_data = None

            for stage in stages:
                res = self._execute_single_command(stage, log_callback, piped_data, tui_data)
                last_result = res
                if res.status == ResultStatus.FAILURE:
                    break
                # Concatenate logs for next stage's piped_data
                piped_data = "\n".join(res.logs)

            return last_result

        return self._execute_single_command(command_str, log_callback, tui_data=tui_data)

    def _execute_single_command(self, command_str: str, log_callback: Optional[Callable[[str], None]] = None, piped_data: Optional[str] = None, tui_data: Optional[dict] = None) -> CommandResult:
        """Internal helper to execute a single (non-piped) command string."""
        parts = shlex.split(command_str)
        if not parts:
            return CommandResult(
                status=ResultStatus.FAILURE,
                message="Empty command stage.",
                error_code="EMPTY_COMMAND",
            )

        base_cmd = parts[0]
        cmd_args = parts[1:]
        handler = self.get_handler(base_cmd)

        if handler is None:
            return CommandResult(
                status=ResultStatus.FAILURE,
                message=f"Unknown command: '{base_cmd}'",
                error_code="UNKNOWN_COMMAND",
            )

        canonical = self._aliases.get(base_cmd, base_cmd)
        if canonical in self._disabled:
             return CommandResult(
                status=ResultStatus.FAILURE,
                message=f"'{base_cmd}' is disabled.",
                error_code="DISABLED_COMMAND",
            )

        # Interactive commands are now handled via internal routing or modal screens
        # so we let them proceed to execution here.

        # Prepare arguments (Try parsing if setup_parser exists)
        mock_args = MockArgs(cmd_args, piped_data=piped_data, tui_data=tui_data)
        setup_parser_func = self._arguments.get(canonical)
        if setup_parser_func:
            import argparse
            class SilentParser(argparse.ArgumentParser):
                def error(self, message): raise ValueError(message)
                def exit(self, status=0, message=None): raise ValueError(message or f"Exit {status}")

            parser = SilentParser(prog=base_cmd, add_help=False)
            try:
                setup_parser_func(parser)
                parsed_args = parser.parse_args(cmd_args)
                setattr(parsed_args, 'piped_data', piped_data)
                setattr(parsed_args, 'tui_data', tui_data)
                setattr(parsed_args, '_tokens', cmd_args)
                mock_args = parsed_args
            except Exception:
                pass # Fallback to MockArgs

        start = time.time()
        capture = StreamingIO(callback=log_callback)

        try:
            import inspect
            sig = inspect.signature(handler)

            with contextlib.redirect_stdout(capture), \
                 contextlib.redirect_stderr(capture):
                # Check if it's a bound method or has 1+ parameters
                if len(sig.parameters) > 0:
                    result = handler(mock_args)
                else:
                    result = handler()

            elapsed = time.time() - start
            captured = capture.getvalue()
            if isinstance(result, CommandResult):
                if not result.duration:
                    result.duration = elapsed
                if captured:
                    result.logs.append(captured)
                return result

            # Legacy path: wrap captured output and result if it's a string
            msg = f"'{base_cmd}' completed."
            logs = [captured] if captured else []

            if isinstance(result, str):
                if not logs:
                    logs = [result]
                else:
                    # If we had prints AND a return value, the return value is likely
                    # the "intended" output for piping. Append it.
                    if result.strip():
                        logs.append(result)
                    msg = "Completed with mixed output."

            return CommandResult(
                status=ResultStatus.SUCCESS,
                message=msg,
                logs=logs,
                duration=elapsed,
            )

        except Exception as exc:
            return CommandResult(
                status=ResultStatus.FAILURE,
                message=str(exc),
                logs=[capture.getvalue()],
                duration=time.time() - start,
                error_code=type(exc).__name__,
            )



    def configure_parsers(self, subparsers):
        """Configure argparse subparsers for all registered commands."""
        for name, handler in self._commands.items():
            # Find aliases for this command
            cmd_aliases = [k for k, v in self._aliases.items() if v == name]
            desc = self._descriptions.get(name, "")

            # Create subparser
            parser = subparsers.add_parser(name, help=desc, aliases=cmd_aliases)
            parser.set_defaults(func=handler)

            # Setup arguments if provided
            if name in self._arguments and self._arguments[name]:
                self._arguments[name](parser)

    def load_plugins(self):
        """Load plugins from entry points, local skills, and local config."""
        # 1. Entry Points (Standard Plugins)
        try:
            # Python 3.10+
            eps = importlib.metadata.entry_points(group="jcapy.plugins")
        except TypeError:
            # Fallback for older python
            eps = importlib.metadata.entry_points().get("jcapy.plugins", [])

        for ep in eps:
            try:
                plugin = ep.load()
                if hasattr(plugin, "register_commands"):
                    plugin.register_commands(self)
            except Exception as e:
                # We don't want to crash CLI if a plugin is broken
                print(f"ValueError loading plugin {ep.name}: {e}")

        # 2. Project Skills (ASI05, 2.1)
        from jcapy.core.skills import get_skill_registry
        registry = get_skill_registry()
        registry.discover()

        for skill in registry.list_skills():
            try:
                manifest = skill.manifest
                if manifest.entry_point:
                    self._load_single_plugin(skill.path, os.path.join(skill.path, "jcapy.yaml"))
            except Exception as e:
                print(f"Warning: Failed to load skill '{skill.manifest.name}': {e}")

    def load_local_plugins(self, plugins_dir: str):
        """
        Load plugins from a directory containing subdirectories with 'jcapy.yaml'.
        """
        if not os.path.exists(plugins_dir):
            return

        for item in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, item)
            manifest_path = os.path.join(plugin_path, "jcapy.yaml")

            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    self._load_single_plugin(plugin_path, manifest_path)
                except Exception as e:
                    # verbose logging here ideally
                    pass

    def _load_single_plugin(self, plugin_dir: str, manifest_path: str):
        """Helper to load a single plugin from a directory."""
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        entry_point = manifest.get("entry_point")
        if not entry_point:
            return

        module_path = os.path.join(plugin_dir, entry_point)
        if not os.path.exists(module_path):
            return

        # Dynamic Import
        module_name = f"jcapy.plugins.local.{manifest.get('name', 'unknown')}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "register_commands"):
                module.register_commands(self)

            if hasattr(module, "register_widgets"):
                from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
                module.register_widgets(WidgetRegistry)

_registry = CommandRegistry()

def get_registry() -> CommandRegistry:
    return _registry
