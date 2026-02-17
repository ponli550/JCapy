# SPDX-License-Identifier: Apache-2.0
from jcapy.core.base import CommandBase


class ManageCommand(CommandBase):
    name = "manage"
    description = "Manage MCP servers, widgets, plugins, and layouts"
    aliases = []

    def setup_parser(self, parser):
        """No arguments needed for manage command."""
        pass

    def execute(self, args):
        """Launch the management interface within the main JCapy App."""
        try:
            from jcapy.commands.core_cmd import run_tui
            run_tui(start_screen="management")

        except Exception as e:
            print(f"\n❌ Error launching management interface: {e}")
            return
