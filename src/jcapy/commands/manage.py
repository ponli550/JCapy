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
        """Launch the management interface."""
        try:
            from jcapy.ui.screens.management_screen import ManagementScreen
            from textual.app import App

            class ManagementApp(App):
                def on_mount(self):
                    self.push_screen(ManagementScreen())

            app = ManagementApp()
            app.run()

        except ImportError as e:
            print(f"\n❌ Management Interface Error: {e}")
            if "textual" in str(e):
                print("💡 Missing 'textual' library. Install with: pip install textual")
            return
        except Exception as e:
            print(f"\n❌ Error launching management interface: {e}")
            return
