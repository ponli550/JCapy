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
    def __init__(self, name: str, description: str, enabled: bool = True, column: str = ""):
        super().__init__()
        self.widget_name = name
        self.description = description
        self.enabled = enabled
        self.column = column
        self.can_focus = True

    def compose(self) -> ComposeResult:
        status = "✓" if self.enabled else "✗"
        col_tag = f" [dim]({self.column[0].upper()})[/dim]" if self.enabled else ""
        yield Label(f"{status} {self.widget_name}{col_tag}", classes="item-label")

    def on_click(self) -> None:
        """Handle click to toggle widget."""
        if self.enabled:
            # Simple toggle off
            self.screen.remove_widget_from_layout(self.widget_name)
        else:
            # Prompt for column
            self.screen.prompt_for_column(self.widget_name)

class ColumnSelectModal(ModalScreen[str]):
    """Modal to select dashboard column for a widget."""
    CSS = """
    ColumnSelectModal {
        align: center middle;
    }
    #col-dialog {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #col-buttons {
        layout: horizontal;
        height: auto;
        margin-top: 1;
        content-align: center middle;
    }
    #col-buttons Button {
        margin: 0 1;
    }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="col-dialog"):
            yield Label("Select Dashboard Column", id="col-title")
            with Horizontal(id="col-buttons"):
                yield Button("Left", id="left_col")
                yield Button("Center", id="center_col")
                yield Button("Right", id="right_col")
            yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            self.dismiss(event.button.id)
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


class ThemeItem(ListItem):
    """A theme selection item with live preview."""
    def __init__(self, name: str, focus_colors: dict):
        super().__init__()
        self.theme_name = name
        self.focus_colors = focus_colors

    def compose(self) -> ComposeResult:
        # Initial display
        yield Label(f"🎨 {self.theme_name.capitalize()}", classes="item-label")

    def on_focus(self) -> None:
        """Apply preview style on focus."""
        bg = self.focus_colors.get("accent", "#007acc")
        self.styles.background = f"{bg} 20%"
        self.styles.border = ("round", bg)
        # We could also notify the app to temporarily preview, but specific widget preview is safer.
        self.query_one(Label).styles.color = bg

    def on_blur(self) -> None:
        """Reset style on blur."""
        self.styles.background = None
        self.styles.border = None
        self.query_one(Label).styles.color = None

    def on_click(self) -> None:
        """Apply the theme permanently."""
        from jcapy.config import set_ux_preference
        set_ux_preference("theme", self.theme_name)
        self.app.notify(f"Theme '{self.theme_name}' applied!", severity="success")
        # App will react via ConfigUpdated


class ManagementScreen(Screen):
    """Management interface for MCP servers, widgets, plugins, and layouts."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "switch_to_dashboard", "Dashboard", show=True),
        Binding("escape", "switch_to_dashboard", "Back", show=True),
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
        grid-size: 3;
        grid-columns: 1fr 1fr 1fr;
        grid-gutter: 2;
        height: 1fr;
        padding: 2;
    }

    .column {
        height: 100%;
        padding: 1 2;
        background: $surface 30%;
        border: round $accent 20%;
        margin: 1;
    }

    .column-header {
        text-style: bold;
        color: $accent;
        background: $accent 8%;
        padding: 0 1;
        margin-bottom: 1;
        border-bottom: double $accent;
    }

    .section-header {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 0;
        padding-left: 1;
        background: $boost 3%;
        border-left: solid $accent;
    }

    .column ListView {
        height: 1fr;
        border: none;
        margin-top: 0;
        background: transparent;
    }

    .column Button {
        width: 100%;
        margin-top: 1;
        margin-bottom: 0;
    }

    .item-label {
        width: 100%;
        padding: 0 1;
    }

    ListItem {
        height: auto;
        padding: 0;
        margin: 0 1;
        transition: background 200ms, tint 200ms;
    }

    ListItem:hover {
        background: $accent 10%;
        tint: $accent 5%;
    }

    ListItem:focus {
        background: $accent 20%;
        border: solid $accent;
        tint: $accent 8%;
        text-style: bold;
    }

    ListItem.-active {
        background: $accent 35%;
    }

    .enabled {
        color: $success;
    }

    .disabled {
        color: $error;
    }

    #danger-zone {
        margin-top: 2;
        padding: 1;
        border: tall $error 20%;
        background: $error 8%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-grid"):
            # Column 1: MCP Servers
            with Vertical(classes="column", id="mcp-column"):
                yield Label("🔌 [bold]MCP Servers[/bold]", classes="column-header")
                yield ListView(id="mcp-list")
                yield Button("+ Add Server", variant="success", id="add-mcp-server")

            # Column 2: Widgets & Plugins (Merged for spatial focus)
            with Vertical(classes="column", id="content-column"):
                yield Label("🧩 [bold]Workspace Elements[/bold]", classes="column-header")
                yield Label("Widgets", classes="section-header")
                yield ListView(id="widget-list")
                yield Label("Plugins", classes="section-header")
                yield ListView(id="plugin-list")
                yield Button("+ Install Plugin", variant="success", id="install-plugin")

            # Column 3: Themes & Systems
            with Vertical(classes="column", id="system-column"):
                yield Label("🎨 [bold]App Systems[/bold]", classes="column-header")
                yield Label("Theme Gallery", classes="section-header")
                yield ListView(id="theme-list")

                with Vertical(id="danger-zone"):
                    yield Label("Management", classes="section-header")
                    yield Button("Save Layout", variant="primary", id="save-layout")
                    yield Button("Reset Layout", variant="warning", id="reset-layout")
                    yield Static(id="layout-info")

                yield Button("⬅️ Back to Dashboard", variant="default", id="btn-back")

        yield Footer()

    def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.load_mcp_servers()
        self.load_widgets()
        self.load_plugins()
        self.load_themes()
        self.load_layout_info()

    def load_themes(self) -> None:
        """Load available themes."""
        theme_list = self.query_one("#theme-list", ListView)
        theme_list.clear()

        from jcapy.ui.theme import THEMES
        for name, colors in THEMES.items():
            theme_list.append(ThemeItem(name, colors))

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
        """Load installed widgets with categorization."""
        widget_list = self.query_one("#widget-list", ListView)
        widget_list.clear()

        from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()

        # Build reverse map for easy lookup
        active_widgets = {}
        for col_name, widgets in layout.items():
            for w in widgets:
                active_widgets[w] = col_name

        # Group widgets by category
        categories = {}
        for name, metadata in WidgetRegistry.get_all_metadata().items():
            cat = metadata.get("category", "Misc")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name, metadata))

        # Render grouped with headers
        for cat in sorted(categories.keys()):
            # Category Header (Non-selectable item)
            header = ListItem(Label(f"[dim]── {cat} ──[/dim]", classes="item-label"), disabled=True)
            widget_list.append(header)

            for name, metadata in sorted(categories[cat]):
                is_active = name in active_widgets
                col = active_widgets.get(name, "")
                widget_list.append(WidgetItem(
                    name=name,
                    description=metadata.get("description", "No description"),
                    enabled=is_active,
                    column=col
                ))

    def prompt_for_column(self, widget_name: str) -> None:
        """Show modal to select column."""
        def handle_choice(choice):
            if choice:
                self.add_widget_to_layout(widget_name, choice)

        self.app.push_screen(ColumnSelectModal(), handle_choice)

    def add_widget_to_layout(self, widget_name: str, column: str) -> None:
        """Add a widget to a specific column in the config."""
        from jcapy.config import get_dashboard_layout, set_dashboard_layout
        layout = get_dashboard_layout()

        # Remove from any existing first
        for col in layout:
            if widget_name in layout[col]:
                layout[col].remove(widget_name)

        # Add to selected
        if column in layout:
            layout[column].append(widget_name)

        set_dashboard_layout(layout)
        self.app.notify(f"Added {widget_name} to {column}")

        # FIX: Defer refresh to avoid "suicidal" event crash
        # Rebuilding the list in the middle of a click event from a soon-to-be-deleted
        # ListItem causes ListView to lose track of its nodes.
        self.call_after_refresh(self.load_widgets)
        self.call_after_refresh(self.load_layout_info)

    def remove_widget_from_layout(self, widget_name: str) -> None:
        """Remove widget from config."""
        from jcapy.config import get_dashboard_layout, set_dashboard_layout
        layout = get_dashboard_layout()

        removed = False
        for col in layout:
            if widget_name in layout[col]:
                layout[col].remove(widget_name)
                removed = True

        if removed:
            set_dashboard_layout(layout)
            self.app.notify(f"Removed {widget_name} from dashboard")

            # FIX: Defer refresh to avoid "suicidal" event crash
            self.call_after_refresh(self.load_widgets)
            self.call_after_refresh(self.load_layout_info)

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

    def action_switch_to_dashboard(self) -> None:
        """Switch back to the dashboard."""
        self.app.switch_screen("dashboard")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-back":
            self.action_switch_to_dashboard()

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
