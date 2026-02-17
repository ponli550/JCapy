from textual.screen import Screen
from textual.widgets import Static, Button, TextArea, ListView, ListItem, Label, DirectoryTree, RichLog, Input, Header, Footer
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, Grid, Container
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.reactive import reactive
import uuid
from jcapy.config import get_dashboard_layout, set_dashboard_layout
from jcapy.ui.messages import ConfigUpdated
from jcapy.ui.widgets.dashboard_widgets import (
    ClockWidget,
    KanbanWidget,
    ProjectStatusWidget,
    MarketplaceWidget,
    MCPWidget,
    GitLogWidget,
    NewsWidget,
    UsageTrackerWidget,
    ScratchpadWidget,
    StatusWidget,
    WidgetRegistry
)

JCAPY_LOGO_COMPACT = """
 [bold cyan]JCapy[/] [dim]v2.0[/]
 [bold blue]━━━━━[/]
"""

from jcapy.ui.screens.widget_catalog import WidgetCatalogScreen

class DashboardScreen(Screen):
    """The main dashboard screen."""

    edit_mode = reactive(False)
    selected_widget_id = reactive(None)
    selected_widget_name = reactive(None)
    is_right_col_collapsed = reactive(False)
    zen_mode = reactive(False)

    BINDINGS = [
        Binding("e", "toggle_edit_mode", "Toggle Edit Layout"),
        Binding("c", "toggle_right_col", "Toggle Marketplace"),
        Binding("+", "add_widget", "Add (+)", show=False),
        Binding("-", "remove_widget", "Remove (-)", show=False),
        Binding("x", "remove_widget", "Remove (x)", show=False),
        # Navigation
        Binding("space", "select_widget", "Select Widget"),
        Binding("h,left", "focus_left", "Focus Left", show=False),
        Binding("l,right", "focus_right", "Focus Right", show=False),
        Binding("j,down", "focus_down", "Focus Down", show=False),
        Binding("k,up", "focus_up", "Focus Up", show=False),
        Binding("z", "toggle_zen_mode", "Zen Mode"),
    ]

    CSS = """
    DashboardScreen.edit-mode-active {
        background: #0a192f;
    }

    DashboardScreen.zen-mode-active #sidebar,
    DashboardScreen.zen-mode-active #left-col,
    DashboardScreen.zen-mode-active #right-col {
        display: none;
    }

    DashboardScreen.zen-mode-active #main-area {
        grid-size: 1;
        grid-columns: 1fr;
        padding: 0;
    }

    DashboardScreen.zen-mode-active #center-col {
        border: none;
        background: transparent;
    }

    #sidebar {
        width: 26;
        height: 100%;
        background: $boost 10%;
        border-right: tall $accent 20%;
        padding: 1;
        dock: left;
    }

    #main-area {
        layout: grid;
        grid-size: 3;
        grid-columns: 1.2fr 2.5fr 1fr;
        grid-gutter: 2;
        padding: 1 2;
        height: 1fr;
    }

    #main-area.right-collapsed {
        grid-columns: 1.2fr 2.5fr 5;
    }

    #left-col, #center-col, #right-col {
        background: $surface 40%;
        border: round $accent 30%;
        padding: 1 2;
        margin: 1;
        height: 100%;
        overflow-y: auto;
    }

    /* Glass Zones */
    #left-col {
        background: $surface 45%;
    }
    #center-col {
        background: $surface 35%;
        border: tall $accent 20%;
    }
    #right-col {
        background: $surface 45%;
    }

    #right-col.collapsed {
        width: 5;
        overflow: hidden;
        border-right: none;
        background: $boost 30%;
    }

    .selected-widget {
        border: double $success !important;
        background: $success 10%;
        opacity: 0.9;
    }

    .logo {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    .nav-header {
        color: $text 50%;
        margin: 1 0;
    }

    #btn-manage {
        margin-top: 1;
        background: $accent 20%;
        border: none;
    }

    #sidebar Button:hover {
        background: $accent 40%;
    }

    /* Kanban specific interactive styles */
    .kanban-col {
        width: 1fr;
        border: solid $surface-lighten-1;
        margin: 0 1;
        background: $surface 10%;
    }

    .kanban-col:focus-within {
        border: double $accent 50%;
        background: $accent 5%;
    }

    .col-header {
        width: 100%;
        content-align: center middle;
        background: $boost;
        text-style: bold;
        padding: 0 1;
        color: $text;
    }

    ListView:focus {
        border: none;
        background: $accent 10%;
    }

    .hidden {
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        layout = get_dashboard_layout()

        # Sidebar (Logo + Context)
        with Vertical(id="sidebar"):
            yield Static(JCAPY_LOGO_COMPACT, classes="logo")
            yield StatusWidget()
            yield Static("⎯⎯⎯⎯⎯⎯ [dim]Navigation[/] ⎯⎯⎯⎯⎯⎯", classes="nav-header")
            # We don't use dynamic layout for sidebar yet, keeping it as a steady anchor
            yield ClockWidget()
            yield ProjectStatusWidget()

            # Static Controls (moved to sidebar bottom)
            yield Static("\n" * 1)
            yield Button("⚙️  Manage", id="btn-manage", variant="default")
            yield Button("🔍 Find", id="btn-find", variant="primary")
            yield Button("🚪 Quit", id="btn-quit", variant="error")

        # Main Workspace
        with Grid(id="main-area"):
            # Left Column (FileExplorer, etc)
            with Vertical(id="left-col"):
                for w_name in layout.get("left_col", []):
                    # Filter out widgets moved to sidebar to avoid duplication
                    if w_name not in ["Clock", "ProjectStatus"]:
                        yield self._create_widget(w_name)

            # Center Column (Kanban)
            with Vertical(id="center-col"):
                for w_name in layout.get("center_col", []):
                    yield self._create_widget(w_name)

            # Right Column (Marketplace, Usage, etc)
            with Vertical(id="right-col"):
                for w_name in layout.get("right_col", []):
                    yield self._create_widget(w_name)

        yield Footer()
        from jcapy.ui.widgets.dashboard_widgets import ConsoleDrawer
        yield ConsoleDrawer(id="dashboard-console")

    def _create_widget(self, name):
        """Factory method for widgets using Registry."""
        widget_cls = WidgetRegistry.get(name)
        if widget_cls:
            # We enforce id convention w-Name-UUID for uniqueness
            unique_id = str(uuid.uuid4())[:8]
            return widget_cls(id=f"w-{name}-{unique_id}")

        # Skip unknown widgets gracefully
        return None

    def on_mount(self):
        # Initial states
        self._refresh_grid_layout()

    def on_resize(self) -> None:
        """Handle terminal resize."""
        self._refresh_grid_layout()

    def _refresh_grid_layout(self) -> None:
        """Update grid columns based on active widgets and terminal width."""
        layout = get_dashboard_layout()
        has_left = len(layout.get("left_col", [])) > 0
        has_center = len(layout.get("center_col", [])) > 0
        has_right = len(layout.get("right_col", [])) > 0

        # Build column spec
        cols = []

        # Responsive: Switch to 1 column if narrow
        is_narrow = self.size.width < 80

        if is_narrow:
            cols = ["1fr"]
        else:
            if has_left: cols.append("1.2fr")
            if has_center: cols.append("2.5fr")
            if has_right: cols.append("1fr")

        # Fallback if everything empty
        if not cols:
            cols = ["1fr"]

        try:
            area = self.query_one("#main-area")
            area.styles.grid_size = len(cols)
            area.styles.grid_columns = " ".join(cols)

            # Show/Hide columns
            # In narrow mode, we don't hide, they just stack (if we use Vertical)
            # Actually, main-area IS a Grid. If grid-size is 1, they stack automatically.
            self.query_one("#left-col").set_class(not has_left, "hidden")
            self.query_one("#center-col").set_class(not has_center, "hidden")
            self.query_one("#right-col").set_class(not has_right, "hidden")
        except:
            pass

    def watch_edit_mode(self, active: bool) -> None:
        """Handle visual changes when edit mode toggles."""
        if not active:
            self._clear_selection()

        # Notify user (state change)
        self.notify(f"Edit Mode: {'ON' if active else 'OFF'}")

        # Update all widgets
        for widget in self.query("*"):
            if hasattr(widget, "toggle_highlight"):
                widget.toggle_highlight(active)

        else:
            self.remove_class("edit-mode-active")

    def watch_zen_mode(self, active: bool) -> None:
        """Handle visual changes when zen mode toggles."""
        self.set_class(active, "zen-mode-active")
        status = "ON" if active else "OFF"
        self.notify(f"Zen Mode: {status}", severity="information")

    def action_toggle_zen_mode(self) -> None:
        """Toggle the Zen focus mode."""
        self.zen_mode = not self.zen_mode

    def action_toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.add_class("edit-mode-active")
        else:
            self.remove_class("edit-mode-active")

    async def on_click(self, event: Click) -> None:
        if not self.edit_mode:
            return

        # Find which widget was clicked
        widget = event.widget
        # Walk up to find the container widget we care about
        # (Since event might correspond to internal Static or Panel)
        target = None
        for w in [widget] + list(widget.ancestors):
            if w.id and w.id.startswith("w-"):
                target = w
                break

        if not target:
            return

        # ID Format: w-Name-UUID or w-Name (legacy)
        parts = target.id.split("-")
        if len(parts) >= 2:
            w_name = parts[1]
        else:
            return # Invalid ID format

        if self.selected_widget_id is None:
            # Select first widget
            self.selected_widget_id = target.id
            self.selected_widget_name = w_name
            target.add_class("selected-widget")
            self.notify(f"Selected: {w_name}. Click another to swap.")
        else:
            # Swap!
            target_name = w_name
            if target.id == self.selected_widget_id:
                self._clear_selection()
                self.notify("Deselected.")
                return

            self._swap_widgets(self.selected_widget_name, target_name)
            self._clear_selection()
            self.edit_mode = False # Exit edit mode after swap

            self.notify(f"Swapped {self.selected_widget_name} <-> {target_name}.")

            # Restart dashboard to apply changes (simplest way)
            # In Textual, we might need to reinstall screen or rebuild it.
            # self.app.uninstall_screen... install... push...
            # For now, let's just notify and ask user to restart or implement a 're-compose' if possible.
            # Actually, `self.app.install_screen(DashboardScreen(), 'dashboard')` overrides?
            # Let's try to just notify for now.
            self.notify(f"Swapped {self.selected_widget_name} <-> {target_name}. Restart to see changes.")
            # OR better: triggers a re-mount if we can.

    def _clear_selection(self):
        """Removes visual selection from all widgets."""
        for widget in self.query(".selected-widget"):
            widget.remove_class("selected-widget")
        self.selected_widget_id = None
        self.selected_widget_name = None

    def _rebuild_column(self, col_name: str):
        """Rebuilds a column from the current layout config."""
        layout = get_dashboard_layout()
        widgets = layout.get(col_name, [])

        # Normalize ID
        col_id = col_name.replace("_", "-")
        try:
            container = self.query_one(f"#{col_id}")
            # Remove all children
            with self.app.batch_update():
                container.remove_children()
                for w_name in widgets:
                    container.mount(self._create_widget(w_name))
        except:
            self.notify(f"Error rebuilding {col_name}")

    def _swap_widgets(self, name_a, name_b):
        layout = get_dashboard_layout()
        # Find which lists they belong to
        loc_a = None
        loc_b = None

        for col in ["left_col", "center_col", "right_col"]:
            if name_a in layout[col]: loc_a = (col, layout[col].index(name_a))
            if name_b in layout[col]: loc_b = (col, layout[col].index(name_b))

        if loc_a and loc_b:
            col_a, idx_a = loc_a
            col_b, idx_b = loc_b

            # Swap
            layout[col_a][idx_a] = name_b
            layout[col_b][idx_b] = name_a

            set_dashboard_layout(layout)
            self.notify("Layout Saved!")

            # Rebuild affected columns to show changes
            self._rebuild_column(col_a)
            if col_a != col_b:
                self._rebuild_column(col_b)

    def action_add_widget(self):
        if not self.edit_mode or not self.selected_widget_id:
            self.notify("Enter Edit Mode (E) & Select a widget first!")
            return

        # Find column of selected widget
        layout = get_dashboard_layout()
        found_col = None
        for col in ["left_col", "center_col", "right_col"]:
            if self.selected_widget_name in layout.get(col, []):
                found_col = col
                break

        if found_col:
            self.app.push_screen(WidgetCatalogScreen(found_col), self.on_catalog_result)
        else:
            self.notify("Could not identify widget column.")

    def on_catalog_result(self, w_name: str) -> None:
        if not w_name:
            return # Cancelled

        # Add to layout
        layout = get_dashboard_layout()
        # Find column again (state might have changed, but unlikely in modal)
        found_col = None
        for col in ["left_col", "center_col", "right_col"]:
            if self.selected_widget_name in layout.get(col, []):
                found_col = col
                break

        if found_col:
            # Append after selected?
            col_list = layout[found_col]
            # Warning: this inserts based on NAME, which might be ambiguous.
            if self.selected_widget_name in col_list:
                idx = col_list.index(self.selected_widget_name)
                col_list.insert(idx + 1, w_name)
                layout[found_col] = col_list

                set_dashboard_layout(layout)
                self.notify(f"Added {w_name}.")

                # Robust Sync: Rebuild the whole column
                self._rebuild_column(found_col)
                self._clear_selection()

                # Highlight the newly added widget?
                # (Optional, but rebuild makes it easy)
            else:
                 self.notify("Error: Selected widget lost.")

    def action_remove_widget(self):
        if not self.edit_mode or not self.selected_widget_id:
            self.notify("Select a widget to remove!")
            return

        layout = get_dashboard_layout()
        for col in ["left_col", "center_col", "right_col"]:
            if self.selected_widget_name in layout.get(col, []):
                layout[col].remove(self.selected_widget_name)
                set_dashboard_layout(layout)
                self.notify(f"Removed {self.selected_widget_name}.")

                # Remove specific instance
                try:
                    self.query_one(f"#{self.selected_widget_id}").remove()
                    self.selected_widget_id = None
                    self.selected_widget_name = None
                except:
                    self.notify("Error removing widget UI.")

                return

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "btn-quit":
            self.app.exit()
        elif btn_id == "btn-manage":
            self.app.switch_screen("management")
        elif btn_id == "btn-find":
            # Trigger custom action defined in app.py
            self.app.action_toggle_palette()
        # Add other handlers as needed

    def on_config_updated(self, message: ConfigUpdated) -> None:
        """Handle configuration updates."""
        if message.key.startswith("dashboard_layout") or message.key == "*":
            # Refresh layout if layout config changed
            self.notify("Dashboard layout updated!")
            # Rebuild all columns to be safe
            self._rebuild_column("left_col")
            self._rebuild_column("center_col")
            self._rebuild_column("right_col")
            # Dynamic grid refresh
            self._refresh_grid_layout()
    async def on_descendant_focus(self, event) -> None:
        """Expand right column if focus enters it."""
        if self.edit_mode: return
        # Check if focus is inside right-col
        try:
            right_col = self.query_one("#right-col")
            if event.widget in right_col.walk_children():
                self.is_right_col_collapsed = False
        except: pass

    async def on_descendant_blur(self, event) -> None:
        """Potentially collapse right column if focus leaves it."""
        if self.edit_mode: return
        self.call_after_refresh(self._auto_collapse_if_needed)

    def _auto_collapse_if_needed(self) -> None:
        focused = self.app.focused
        if not focused: return
        try:
            # If focus moved to left or center, collapse right-col
            left_center = self.query("#left-col, #center-col")
            for col in left_center:
                if focused in col.walk_children():
                    self.is_right_col_collapsed = True
                    break
        except: pass

    def action_focus_left(self) -> None:
        self.screen.focus_previous() # Basic cycle for now, can improve with geometry

    def action_focus_right(self) -> None:
        self.screen.focus_next()

    def action_focus_down(self) -> None:
        self.screen.focus_next()

    def action_focus_up(self) -> None:
        self.screen.focus_previous()

    def action_select_widget(self) -> None:
        """Show widget picker modal."""
        # Check if we are in an input field (editing text)
        focused = self.app.focused
        if isinstance(focused, (Button, Static)) or focused is None:
             pass # Safe to trigger
        elif str(type(focused)).find("Input") != -1 or str(type(focused)).find("TextArea") != -1:
             return # Don't interrupt typing

        from jcapy.ui.screens.widget_catalog import WidgetCatalogScreen
        # Reuse catalog screen but potentially in a 'select' mode?
        # For now, let's just use it to FIND a widget to focus.
        # Actually WidgetCatalogScreen is for ADDING. We need a 'focus selector'.
        # Let's build a simple bespoke modal here or use CommandPalette logic.

    def action_toggle_palette(self) -> None:
        """Toggle the command palette."""
        self.app.action_toggle_palette()

    def action_toggle_right_col(self) -> None:
        """Toggle the right column (Marketplace)."""
        self.is_right_col_collapsed = not self.is_right_col_collapsed

    def watch_is_right_col_collapsed(self, value: bool) -> None:
        """React to right column collapse change."""
        try:
            area = self.query_one("#main-area")
            col = self.query_one("#right-col")
            area.set_class(value, "right-collapsed")
            col.set_class(value, "collapsed")
        except:
            pass # App might still be mounting
