from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Grid, Vertical, Horizontal
from textual.app import ComposeResult
from jcapy.ui.widgets.dashboard_widgets import (
    ClockWidget,
    WorldMapWidget,
    ProjectStatusWidget,
    MarketplaceWidget,
    MCPWidget
)

JCAPY_LOGO = """
      _  _____
     | |/ ____|
     | | |     __ _ _ __  _   _
 _   | | |    / _` | '_ \| | | |
| |__| | |___| (_| | |_) | |_| |
 \____/ \_____\__,_| .__/ \__, |
                   | |     __/ |
                   |_|    |___/
"""

class DashboardScreen(Screen):
    """The main dashboard screen."""

    CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 3;
        grid-columns: 30 1fr 30;
        grid-rows: 14 1fr 10;
        grid-gutter: 1;
        padding: 1;
    }

    #logo-area {
        column-span: 3;
        height: 100%;
        content-align: center middle;
        background: $boost;
        border: solid $accent;
    }

    #left-col {
        row-span: 1;
    }

    #center-col {
        row-span: 1;
        content-align: center middle;
    }

    #right-col {
        row-span: 1;
    }

    .box {
        height: 100%;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        # Header / Logo Area (Row 1, Span 3)
        with Horizontal(id="logo-area"):
             yield Static(JCAPY_LOGO, classes="logo")
             # Clock floating right? Or just put it here
             yield ClockWidget()

        # Left Column: Project & MCP (Row 2, Col 1)
        with Vertical(id="left-col"):
            yield ProjectStatusWidget()
            yield MCPWidget()

        # Center: World Map (Row 2, Col 2)
        yield WorldMapWidget(id="center-col")

        # Right Column: Marketplace & Actions (Row 2, Col 3)
        with Vertical(id="right-col"):
            yield MarketplaceWidget()
            yield Button("🔍 Find (Ctrl+P)", id="btn-find", variant="primary")
            yield Button("🚪 Quit", id="btn-quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "btn-quit":
            self.app.exit()
        elif btn_id == "btn-find":
            # Trigger custom action defined in app.py
            self.app.action_toggle_palette()
        # Add other handlers as needed
