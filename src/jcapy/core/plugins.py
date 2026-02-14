# SPDX-License-Identifier: Apache-2.0
import importlib.metadata
import os
import yaml
from typing import Dict, Any, Callable, Optional, List

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

    def register(self, name: str, handler: Callable, description: str, aliases: List[str] = None, setup_parser: Callable = None):
        """
        Register a new command.

        Args:
            name: Command name
            handler: Function to call (takes 'args' namespace)
            description: Help text
            aliases: List of alias names
            setup_parser: Function taking (parser) to add arguments
        """
        self._commands[name] = handler
        self._descriptions[name] = description
        self._arguments[name] = setup_parser

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

_registry = CommandRegistry()

def get_registry() -> CommandRegistry:
    return _registry
