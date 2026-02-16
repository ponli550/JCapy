from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static, Input
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding
from rich.panel import Panel
import os
import json
import yaml


class AddServerModal(ModalScreen[dict]):
    """Modal dialog to add a new MCP server."""

    CSS = """
    AddServerModal {
        align: center middle;
    }

    #modal-dialog {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    #modal-buttons {
        align: right middle;
        height: auto;
        margin-top: 1;
    }

    #modal-buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Add New MCP Server", id="modal-title")
            yield Input(placeholder="Server Name (e.g., filesystem)", id="name-input")
            yield Input(placeholder="Command (e.g., npx -y @modelcontextprotocol/server-filesystem)", id="cmd-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Add", variant="success", id="add")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            name = self.query_one("#name-input", Input).value.strip()
            cmd = self.query_one("#cmd-input", Input).value.strip()

            if not name or not cmd:
                self.app.notify("Server name and command are required", severity="error")
                return

            self.dismiss({"name": name, "command": cmd, "enabled": True})
        else:
            self.dismiss(None)


class MCPServerItem(ListItem):
    """An MCP server configuration item."""
    def __init__(self, name: str, command: str, enabled: bool = True):
        super().__init__()
        self.server_name = name
        self.command = command
        self.enabled = enabled
        self.can_focus = True

    def compose(self) -> ComposeResult:
        label = Label(f"{self.server_name}", classes="item-label")
        if self.enabled:
            label.add_class("enabled")
        else:
            label.add_class("disabled")
        yield label

    def on_click(self) -> None:
        """Handle click to show details."""
        self.app.notify(f"MCP Server: {self.server_name}\nCommand: {self.command}\nPress 'e' to edit, 'd' to delete", severity="information", timeout=5)


class WidgetItem(ListItem):
    """An installed widget item."""
    def __init__(self, name: str, description: str, enabled: bool = True):
        super().__init__()
        self.widget_name = name
        self.description = description
        self.enabled = enabled
        self.can_focus = True

    def compose(self) -> ComposeResult:
        status = "✓" if self.enabled else "✗"
        yield Label(f"{status} {self.widget_name}", classes="item-label")

    def on_click(self) -> None:
        """Handle click to toggle widget."""
        self.enabled = not self.enabled
        status = "✓" if self.enabled else "✗"
        label = self.query_one(Label)
        label.update(f"{status} {self.widget_name}")
        action = "enabled" if self.enabled else "disabled"
        self.app.notify(f"Widget '{self.widget_name}' {action}", severity="information")


class PluginItem(ListItem):
    """An installed plugin/skill item."""
    def __init__(self, name: str, version: str, path: str):
        super().__init__()
        self.plugin_name = name
        self.version = version
        self.path = path
        self.can_focus = True

    def compose(self) -> ComposeResult:
        yield Label(f"📦 {self.plugin_name} [dim]v{self.version}[/dim]", classes="item-label")

    def on_click(self) -> None:
        """Handle click to show details."""
        self.app.notify(f"Plugin: {self.plugin_name} v{self.version}\nPath: {self.path}\nPress 'u' to update, 'd' to delete", severity="information", timeout=5)


class ManagementScreen(Screen):
    """Management interface for MCP servers, widgets, plugins, and layouts."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("enter", "activate_item", "Select", show=True),
        Binding("delete", "delete_item", "Delete", show=False),
        Binding("e", "edit_item", "Edit", show=False),
    ]

    CSS = """
    ManagementScreen {
        background: $background;
        layout: vertical;
    }

    #main-grid {
        layout: grid;
        grid-size: 4;
        grid-columns: 1fr 1fr 1fr 1fr;
        grid-gutter: 1;
        height: 1fr;
        padding: 1;
    }

    .column {
        height: 100%;
        border: solid $accent 30%;
        padding: 1;
    }

    .column-header {
        text-style: bold;
        color: $accent;
        background: $boost 10%;
        padding: 0 1;
        margin-bottom: 1;
    }

    .section-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .column ListView {
        height: 1fr;
        border: none;
        margin-top: 1;
    }

    .column Button {
        width: 100%;
        margin-top: 0;
        margin-bottom: 1;
    }

    .item-label {
        width: 100%;
        padding: 0 1;
    }

    ListItem {
        height: auto;
        padding: 0;
    }

    ListItem:hover {
        background: $boost 20%;
    }

    ListItem:focus {
        background: $accent 20%;
    }

    ListItem.-active {
        background: $accent 30%;
    }

    .enabled {
        color: $success;
    }

    .disabled {
        color: $error;
    }

    Static#layout-info {
        height: auto;
        margin-top: 1;
        padding: 1;
        border: solid $accent 20%;
        background: $boost 5%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-grid"):
            # Column 1: MCP Servers
            with Vertical(classes="column", id="mcp-column"):
                yield Label("🔌 [bold]MCP Servers[/bold]", classes="column-header")
                yield Button("+ Add Server", variant="success", id="add-mcp-server")
                yield ListView(id="mcp-list")

            # Column 2: Widgets
            with Vertical(classes="column", id="widget-column"):
                yield Label("🧩 [bold]Widgets[/bold]", classes="column-header")
                yield ListView(id="widget-list")

            # Column 3: Plugins
            with Vertical(classes="column", id="plugin-column"):
                yield Label("📦 [bold]Plugins[/bold]", classes="column-header")
                yield Button("+ Install", variant="success", id="install-plugin")
                yield ListView(id="plugin-list")

            # Column 4: Layouts
            with Vertical(classes="column", id="layout-column"):
                yield Label("🎨 [bold]Layouts[/bold]", classes="column-header")
                yield Button("Save", variant="primary", id="save-layout")
                yield Button("Load", variant="primary", id="load-layout")
                yield Button("Reset", variant="warning", id="reset-layout")
                yield Static(id="layout-info")

        yield Footer()

    def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.load_mcp_servers()
        self.load_widgets()
        self.load_plugins()
        self.load_layout_info()

    def load_mcp_servers(self) -> None:
        """Load MCP server configurations."""
        mcp_list = self.query_one("#mcp-list", ListView)
        mcp_list.clear()  # Prevent duplicates on refresh

        # Mock data - in production, read from config
        servers = [
            MCPServerItem("filesystem", "npx -y @modelcontextprotocol/server-filesystem", True),
            MCPServerItem("github", "npx -y @modelcontextprotocol/server-github", True),
            MCPServerItem("postgres", "npx -y @modelcontextprotocol/server-postgres", True),
        ]

        for server in servers:
            mcp_list.append(server)

    def load_widgets(self) -> None:
        """Load installed widgets."""
        widget_list = self.query_one("#widget-list", ListView)
        widget_list.clear()  # Prevent duplicates on refresh

        from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry

        for name, metadata in WidgetRegistry.get_all_metadata().items():
            widget_list.append(WidgetItem(
                name=name,
                description=metadata.get("description", "No description"),
                enabled=True  # TODO: Track enabled state
            ))

    def load_plugins(self) -> None:
        """Load installed plugins."""
        plugin_list = self.query_one("#plugin-list", ListView)
        plugin_list.clear()  # Prevent duplicates on refresh

        skills_dir = os.path.expanduser("~/.jcapy/skills")
        if os.path.exists(skills_dir):
            for item in os.listdir(skills_dir):
                plugin_path = os.path.join(skills_dir, item)
                if os.path.isdir(plugin_path):
                    # Try to read manifest
                    manifest_path = os.path.join(plugin_path, "jcapy.yaml")
                    version = "unknown"
                    if os.path.exists(manifest_path):
                        try:
                            import yaml
                            with open(manifest_path) as f:
                                manifest = yaml.safe_load(f) or {}
                                version = manifest.get("version", "unknown")
                        except (yaml.YAMLError, IOError, KeyError) as e:
                            # Robust error handling for malformed YAML
                            self.app.notify(f"Warning: Could not read manifest for {item}: {e}", severity="warning")

                    plugin_list.append(PluginItem(
                        name=item,
                        version=version,
                        path=plugin_path
                    ))

    def load_layout_info(self) -> None:
        """Load current layout information."""
        layout_info = self.query_one("#layout-info", Static)

        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()

        info_text = f"""[bold]Current Layout:[/bold]
Left: {len(layout.get('left_col', []))} • Center: {len(layout.get('center_col', []))} • Right: {len(layout.get('right_col', []))}"""

        layout_info.update(info_text)

    def action_refresh(self) -> None:
        """Refresh all lists."""
        self.load_mcp_servers()
        self.load_widgets()
        self.load_plugins()
        self.load_layout_info()
        self.app.notify("Refreshed all lists", severity="information")

    def action_quit(self) -> None:
        """Quit the management screen."""
        self.app.exit()

    def action_activate_item(self) -> None:
        """Activate the focused item (same as clicking it)."""
        focused = self.focused
        if isinstance(focused, (MCPServerItem, WidgetItem, PluginItem)):
            focused.on_click()

    def action_delete_item(self) -> None:
        """Delete the focused item."""
        focused = self.focused
        if isinstance(focused, MCPServerItem):
            self.app.notify(f"Delete MCP server '{focused.server_name}'? (Not implemented)", severity="warning")
        elif isinstance(focused, PluginItem):
            self.app.notify(f"Delete plugin '{focused.plugin_name}'? (Not implemented)", severity="warning")

    def action_edit_item(self) -> None:
        """Edit the focused item."""
        focused = self.focused
        if isinstance(focused, MCPServerItem):
            self.app.notify(f"Edit MCP server '{focused.server_name}' (Not implemented)", severity="information")
        elif isinstance(focused, PluginItem):
            self.app.notify(f"Edit plugin '{focused.plugin_name}' (Not implemented)", severity="information")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "add-mcp-server":
            def handle_server_data(server_data):
                if server_data:
                    mcp_list = self.query_one("#mcp-list", ListView)
                    mcp_list.append(
                        MCPServerItem(server_data['name'], server_data['command'], server_data['enabled'])
                    )
                    self.app.notify(f"Added MCP server '{server_data['name']}'", severity="success")

            self.app.push_screen(AddServerModal(), handle_server_data)
        elif button_id == "install-plugin":
            self.app.notify("Use 'jcapy install <git-url>' to install plugins", severity="information")
        elif button_id == "save-layout":
            self.save_current_layout()
        elif button_id == "load-layout":
            self.app.notify("Layout loading coming soon!", severity="information")
        elif button_id == "reset-layout":
            self.reset_to_default_layout()
        elif button_id and button_id.startswith("toggle-"):
            widget_name = button_id.replace("toggle-", "")
            self.app.notify(f"Widget toggle for {widget_name} coming soon!", severity="information")
        elif button_id and button_id.startswith("remove-"):
            item_name = button_id.replace("remove-", "")
            self.app.notify(f"Remove operation for {item_name} coming soon!", severity="warning")

    def save_current_layout(self) -> None:
        """Save the current dashboard layout."""
        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()

        # Save to a named layout file
        layouts_dir = os.path.expanduser("~/.jcapy/layouts")
        os.makedirs(layouts_dir, exist_ok=True)

        layout_file = os.path.join(layouts_dir, "saved_layout.json")
        with open(layout_file, 'w') as f:
            json.dump(layout, f, indent=2)

        self.app.notify(f"Layout saved to {layout_file}", severity="information")

    def reset_to_default_layout(self) -> None:
        """Reset to the default dashboard layout."""
        from jcapy.config import set_dashboard_layout, DEFAULT_LAYOUT
        set_dashboard_layout(DEFAULT_LAYOUT)
        self.load_layout_info()
        self.app.notify("Layout reset to default", severity="information")
