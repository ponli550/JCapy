from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static
from textual.containers import Vertical, Container
from typing import Optional, List

class TerminalPromptScreen(ModalScreen):
    """
    Transparent overlay for gathering input without suspending the TUI.
    """

    DEFAULT_CSS = """
    TerminalPromptScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #prompt-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        border-title-align: left;
    }

    #options-list {
        margin: 1 0;
        height: auto;
    }

    .option-item {
        color: $text-muted;
    }

    Input {
        margin-top: 1;
        border: tall $accent;
    }
    """

    def __init__(
        self,
        prompt: str,
        choices: Optional[List[str]] = None,
        default: Optional[str] = None,
        **kwargs
    ):
        self.prompt_text = prompt
        self.choices = choices
        self.default_val = default
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Container(id="prompt-container"):
            yield Label(f"[bold cyan]{self.prompt_text}[/]")

            if self.choices:
                with Vertical(id="options-list"):
                    for i, choice in enumerate(self.choices):
                        yield Static(f" [dim]({choice[0]})[/] {choice}", classes="option-item")

            placeholder = f"❯ Default: {self.default_val}" if self.default_val else "❯ Type here..."
            yield Input(placeholder=placeholder, value=self.default_val or "", id="prompt-input")

    def on_mount(self) -> None:
        self.query_one("#prompt-input").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if not val and self.default_val:
            val = self.default_val

        if self.choices:
             # Check for single char matches (e.g. 'y' for 'yes')
             match = None
             for c in self.choices:
                 if val.lower() == c.lower() or (len(val) == 1 and val.lower() == c[0].lower()):
                     match = c
                     break
             if match:
                 self.dismiss(match)
             else:
                 self.notify("Invalid choice", severity="error")
                 return
        else:
            self.dismiss(val)

    def action_cancel(self) -> None:
        self.dismiss(None)
