from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Grid, Vertical, Horizontal
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.reactive import reactive
import uuid
from jcapy.config import get_dashboard_layout, set_dashboard_layout
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
    WidgetRegistry
)

JCAPY_LOGO = """
      _  _____
     | |/ ____|
     | | |     __ _ _ __  _   _
 _   | | |    / _` | '_ \| | | |
| |__| | |___| (_| | |_) | |_| |
 \____/ \_____\__,_ | .__/ \__, |
                   | |     __/ |
                   |_|    |___/
"""

from jcapy.ui.screens.widget_catalog import WidgetCatalogScreen

class DashboardScreen(Screen):
    """The main dashboard screen."""

    edit_mode = reactive(False)
    selected_widget_id = reactive(None)
    selected_widget_name = reactive(None)

    BINDINGS = [
        Binding("e", "toggle_edit_mode", "Toggle Edit Layout"),
        Binding("+", "add_widget", "Add (+)", show=False),
        Binding("-", "remove_widget", "Remove (-)", show=False),
    ]

    CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 2.5fr 1fr;
        grid-rows: 14 1fr 10;
        grid-gutter: 2;
        padding: 1;
        background: $background;
    }

    DashboardScreen.edit-mode-active {
        background: #0a192f; /* Deep Navy Edit Background */
    }

    #logo-area {
        column-span: 3;
        height: 100%;
        content-align: center middle;
        background: $boost 10%;
        border: double $accent 30%;
        margin-bottom: 2;
    }

    #left-col, #center-col, #right-col {
        row-span: 1;
        overflow-y: auto;
        padding: 1;
        background: $surface 20%;
        border: solid $accent 10%;
    }

    #center-col {
        background: $surface 40%;
        border: solid $accent 30%;
    }

    .selected-widget {
        border: double $success !important;
        background: $success 10%;
        opacity: 0.9;
    }

    .logo {
        color: $accent;
        text-style: bold;
    }

    /* Kanban specific interactive styles */
    .kanban-col {
        width: 1fr;
        border: solid $surface;
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
    }

    ListView:focus {
        border: none;
        background: $accent 10%;
    }
    """

    def compose(self) -> ComposeResult:
        layout = get_dashboard_layout()

        # Header / Logo Area (Row 1, Span 3)
        with Horizontal(id="logo-area"):
             yield Static(JCAPY_LOGO, classes="logo")

        # Dynamic Columns
        with Vertical(id="left-col"):
            for w_name in layout.get("left_col", []):
                yield self._create_widget(w_name)

        # Center Column
        with Vertical(id="center-col"): # Wrapped in Vertical for consistency
            for w_name in layout.get("center_col", []):
                yield self._create_widget(w_name)

        # Right Column
        with Vertical(id="right-col"):
            for w_name in layout.get("right_col", []):
                yield self._create_widget(w_name)

            # Static Controls (always at bottom right)
            yield Button("🔍 Find (Ctrl+P)", id="btn-find", variant="primary")
            yield Button("🚪 Quit", id="btn-quit", variant="error")

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

        # Fallback
        return Static(f"Unknown Widget: {name}")

    def on_mount(self):
        # Initial states
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
        elif btn_id == "btn-find":
            # Trigger custom action defined in app.py
            self.app.action_toggle_palette()
        # Add other handlers as needed
