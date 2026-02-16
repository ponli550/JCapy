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

        self._commands[name] = handler
        self._descriptions[name] = description
        self._arguments[name] = setup_parser

        if interactive:
            self._interactive.add(name)

        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get the handler for a command, resolving aliases."""
        if name in self._commands:
            return self._commands[name]

        if name in self._aliases:
            real_name = self._aliases[name]
            return self._commands.get(real_name)

        return None

    def get_commands(self) -> Dict[str, str]:
        """Return all registered commands and descriptions."""
        return self._descriptions.copy()

    # ------------------------------------------------------------------
    # Shared Engine: Unified Dispatcher (CLI + TUI)
    # ------------------------------------------------------------------

    def execute_string(self, command_str: str) -> CommandResult:
        """
        Parse a raw command string and execute it via the registry.

        This is the single entry-point for both the TUI Command Palette
        and any programmatic callers.  It handles:
          - Legacy commands that print() to stdout  → captured & wrapped
          - Modern commands that return CommandResult → passed through
        """
        parts = shlex.split(command_str)
        if not parts:
            return CommandResult(
                status=ResultStatus.FAILURE,
                message="Empty command.",
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

        # Resolve canonical name for interactive check (aliases → real name)
        canonical = self._aliases.get(base_cmd, base_cmd)
        if canonical in self._interactive:
            return CommandResult(
                status=ResultStatus.WARNING,
                message=f"'{base_cmd}' requires interactive input. Run from terminal: jcapy {' '.join(parts)}",
                error_code="INTERACTIVE_COMMAND",
            )

        # Build a lightweight args namespace so legacy handlers work
        class _Args:
            def __init__(self, tokens: list):
                self._tokens = tokens
            def __getattr__(self, item):
                return None

        mock_args = _Args(cmd_args)

        start = time.time()
        capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(capture), \
                 contextlib.redirect_stderr(capture):
                result = handler(mock_args)

            elapsed = time.time() - start

            # Modern path: handler already returned a CommandResult
            if isinstance(result, CommandResult):
                if not result.duration:
                    result.duration = elapsed
                # Append any captured prints to the result's logs
                captured = capture.getvalue()
                if captured:
                    result.logs.append(captured)
                return result

            # Legacy path: wrap captured output
            return CommandResult(
                status=ResultStatus.SUCCESS,
                message=f"'{base_cmd}' completed.",
                logs=[capture.getvalue()],
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
        for name, desc in self._commands.items():
            # Find aliases for this command
            cmd_aliases = [k for k, v in self._aliases.items() if v == name]

            # Create subparser
            parser = subparsers.add_parser(name, help=desc, aliases=cmd_aliases)
            parser.set_defaults(func=self._commands[name])

            # Setup arguments if provided
            if name in self._arguments and self._arguments[name]:
                self._arguments[name](parser)

    def load_plugins(self):
        """Load plugins from entry points and local config."""
        # 1. Entry Points
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
                print(f"ValuesError loading plugin {ep.name}: {e}")

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

_registry = CommandRegistry()

def get_registry() -> CommandRegistry:
    return _registry
