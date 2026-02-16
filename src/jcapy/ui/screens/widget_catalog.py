from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static
from textual.containers import Vertical, Horizontal, Container
from rich.text import Text
from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry

class WidgetCatalogScreen(ModalScreen):
    """Screen to select a widget from the registry."""

    CSS = """
    WidgetCatalogScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }

    #dialog {
        padding: 1 2;
        width: 70;
        height: 85%;
        border: solid $accent 30%;
        background: $surface;
        shadow: box 0 0 10 2 rgba(0,0,0,0.5);
    }

    ListView {
        height: 1fr;
        border: solid $accent 10%;
        margin: 1 0;
        background: transparent;
    }

    ListItem {
        padding: 1;
        background: $boost 50%;
        margin-bottom: 1;
        border: solid $accent 5%;
    }

    ListItem:hover {
        background: $accent-darken-3;
        border: solid $accent 40%;
    }

    .widget-name {
        text-style: bold;
        color: $accent;
    }

    .widget-desc {
        text-style: italic;
        color: $text-muted;
    }

    .size-badge {
        color: $text;
        padding: 0 1;
        text-style: bold;
        border-radius: 1;
    }

    .size-small { background: $success 20%; color: $success; }
    .size-large { background: $warning 20%; color: $warning; }
    .size-flexible { background: $secondary 20%; color: $secondary; }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    """

    def __init__(self, target_slot: str, current_widget: str = None):
        super().__init__()
        self.target_slot = target_slot
        self.current_widget = current_widget

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Select Widget for {self.target_slot.title()}", id="title")

            widgets = WidgetRegistry.get_all_metadata()
            items = []

            for name, meta in widgets.items():
                size = meta.get("size", "flexible")
                desc = meta.get("description", "No description")

                # Check compatibility warnings (simple for now)
                # e.g. Large widget in side column
                warning = ""
                if size == "large" and self.target_slot in ["left_col", "right_col"]:
                    warning = " ⚠️ Too wide?"

                items.append(
                    ListItem(
                        Vertical(
                            Horizontal(
                                Label(name, classes="widget-name"),
                                Label(f" [{size.upper()}]", classes=f"size-badge size-{size}"),
                                classes="header-row"
                            ),
                            Label(f"{desc}{warning}", classes="widget-desc")
                        ),
                        id=f"item-{name}"
                    )
                )

            yield ListView(*items, id="widget-list")
            yield Button("Cancel", variant="error", id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Extract widget name from ID item-Name
        w_name = event.item.id.replace("item-", "")
        self.dismiss(w_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
