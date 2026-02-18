from datetime import datetime
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button, Input, Static, ListView, ListItem
from textual.containers import Vertical, Horizontal, Grid, Container
from textual.binding import Binding
from jcapy.config import CONFIG_MANAGER
from jcapy.utils.usage import USAGE_LOG_MANAGER

class BudgetScreen(ModalScreen):
    """
    Modal screen for configuring AI budget and pricing rules.
    """

    DEFAULT_CSS = """
    BudgetScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #budget-container {
        width: 80;
        height: 40;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    .section-title {
        text-align: center;
        background: $accent-darken-2;
        color: white;
        margin: 1 0;
        padding: 0 1;
    }

    .pricing-grid {
        grid-size: 4;
        grid-gutter: 1;
        height: auto;
        border: tall $surface-lighten-1;
        margin-bottom: 1;
        padding: 1;
    }

    .grid-header {
        text-style: bold italic;
        color: $secondary;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
        color: #ffffff !important;
        background: #333333 !important;
    }

    #button-bar {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def safe_id(self, model_name: str, prefix: str = "") -> str:
        """Sanitize model name for use as a widget ID."""
        clean = model_name.replace(".", "_").replace("-", "_")
        return f"{prefix}{clean}"

    def compose(self) -> ComposeResult:
        summary = USAGE_LOG_MANAGER.get_session_summary()
        current_limit = CONFIG_MANAGER.get("usage.session_limit", 5.0)
        rules = USAGE_LOG_MANAGER.pricing_rules

        with Container(id="budget-container"):
            yield Label("[bold magenta]💰 Budget & Pricing Control[/]", classes="section-title")

            # Session Summary
            with Vertical(id="session-summary"):
                yield Label(f"[cyan]SESSION COSTS:[/] [bold]${summary['cost']:.4f}[/]")
                yield Label(f"[dim]Total Hits:[/] {summary['hits']}")
                yield Horizontal(
                    Label("Session Limit ($): "),
                    Input(value=str(current_limit), placeholder="e.g. 10.0", id="session-limit"),
                    classes="limit-row"
                )

            yield Label("[bold cyan]PRICING RULES ($ per 1M tokens)[/]", classes="section-title")

            # Pricing Grid
            with Grid(classes="pricing-grid") as grid:
                yield Label("Model", classes="grid-header")
                yield Label("In Rate", classes="grid-header")
                yield Label("Out Rate", classes="grid-header")
                yield Label("Cache Rate", classes="grid-header")

                for model, rates in rules.items():
                    yield Input(value=model, id=self.safe_id(model, "name-"), placeholder="Model name")
                    yield Input(value=str(rates.get("in", 0)), id=self.safe_id(model, "in-"), placeholder="In rate")
                    yield Input(value=str(rates.get("out", 0)), id=self.safe_id(model, "out-"), placeholder="Out rate")
                    yield Input(value=str(rates.get("cache", 0)), id=self.safe_id(model, "cache-"), placeholder="Cache rate")

                # Add Model Row (Empty)
                yield Input(placeholder="Add new model...", id="add-model-name")
                yield Input(placeholder="0.0", id="add-model-in")
                yield Input(placeholder="0.0", id="add-model-out")
                yield Input(placeholder="0.0", id="add-model-cache")

            with Horizontal(id="button-bar"):
                yield Button("Save & Close", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        # 1. Update Session Limit
        try:
            limit = float(self.query_one("#session-limit").value)
            CONFIG_MANAGER.set("usage.session_limit", limit)
        except ValueError:
            pass

        # 2. Update Pricing Rules
        new_rules = {}
        # Iterate over existing known models to capture renames or rate changes
        for old_model in USAGE_LOG_MANAGER.pricing_rules.keys():
            try:
                # Get the new name from the input field corresponding to the old model key
                new_model_name = self.query_one(f"#{self.safe_id(old_model, 'name-')}").value.strip()
                if not new_model_name:
                    continue # Skip empty names (delete behavior? or just skip)

                in_val = self.query_one(f"#{self.safe_id(old_model, 'in-')}").value
                out_val = self.query_one(f"#{self.safe_id(old_model, 'out-')}").value
                cache_val = self.query_one(f"#{self.safe_id(old_model, 'cache-')}").value

                new_rules[new_model_name] = {
                    "in": float(in_val) if in_val else 0.0,
                    "out": float(out_val) if out_val else 0.0,
                    "cache": float(cache_val) if cache_val else 0.0
                }
            except:
                # Fallback to current rule if input is invalid
                new_rules[old_model] = USAGE_LOG_MANAGER.pricing_rules[old_model]

        # 3. Add New Model Row if name is provided
        try:
            add_name = self.query_one("#add-model-name").value.strip()
            if add_name and add_name not in new_rules:
                in_val = self.query_one("#add-model-in").value
                out_val = self.query_one("#add-model-out").value
                cache_val = self.query_one("#add-model-cache").value

                new_rules[add_name] = {
                    "in": float(in_val) if in_val else 0.0,
                    "out": float(out_val) if out_val else 0.0,
                    "cache": float(cache_val) if cache_val else 0.0
                }
        except:
            pass

        CONFIG_MANAGER.set("usage.pricing", new_rules)
        USAGE_LOG_MANAGER.pricing_rules = new_rules

        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(None)
