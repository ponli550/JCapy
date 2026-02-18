from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static
from textual.containers import Vertical, Container
from textual.binding import Binding
import os

class BrainstormScreen(ModalScreen):
    """
    Modal wizard for selection of target files and AI providers for brainstorming.
    """

    DEFAULT_CSS = """
    BrainstormScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #wizard-container {
        width: 70;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    Label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }

    ListView {
        height: 1fr;
        border: tall $accent;
        margin: 1 0;
    }

    ListItem {
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step = 1
        self.selected_file = None
        self.selected_provider = None

        # 1. Discover Files
        self.files = [f for f in os.listdir('.') if f.endswith('.md') or f.endswith('.py') or f.endswith('.sh')]
        self.providers = ["local", "gemini", "openai", "deepseek"]

    def compose(self) -> ComposeResult:
        with Container(id="wizard-container"):
            yield Label("[bold magenta]🧠 Brainstorm Wizard[/]")
            yield Label("[cyan]Phase 1: Select Target File[/]", id="step-title")

            with Vertical(id="selection-area"):
                with ListView(id="file-list"):
                    for f in self.files:
                        yield ListItem(Static(f"📄 {f}"))

                with ListView(id="provider-list") as provider_list:
                    provider_list.display = False
                    for p in self.providers:
                        yield ListItem(Static(f"🤖 {p.upper()}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if self.step == 1:
            # File selected
            idx = self.query_one("#file-list").index
            self.selected_file = self.files[idx]

            # Transition to Step 2
            self.step = 2
            self.query_one("#file-list").display = False
            self.query_one("#provider-list").display = True
            self.query_one("#step-title").update("[cyan]Phase 2: Select Intelligence Engine[/]")
            self.query_one("#provider-list").focus()

        elif self.step == 2:
            # Provider selected
            idx = self.query_one("#provider-list").index
            self.selected_provider = self.providers[idx]

            # Finalize
            self.dismiss((self.selected_file, self.selected_provider))

    def action_cancel(self) -> None:
        self.dismiss(None)
