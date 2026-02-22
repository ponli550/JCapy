from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

class ApprovalScreen(ModalScreen[bool]):
    """
    A premium modal for confirming sensitive tool executions.
    Follows the 'Glass-Box' principle by showing the full command and description.
    """

    BINDINGS = [
        Binding("y", "approve", "Approve"),
        Binding("n", "deny", "Deny"),
        Binding("escape", "deny", "Cancel"),
    ]

    def __init__(self, command: str, description: str = "This command may modify your system or files."):
        super().__init__()
        self.command = command
        self.description = description

    def compose(self) -> ComposeResult:
        with Vertical(id="approval-dialog", classes="glass"):
            yield Static("🛡️ [bold cyan]TOOL APPROVAL REQUIRED[/bold cyan]", id="approval-title")
            yield Static(f"\n[dim]The agent wants to run:[/]", classes="approval-label")
            yield Static(f"[bold white on red] {self.command} [/]", id="approval-cmd")
            yield Static(f"\n[dim]Purpose:[/]\n[italic]{self.description}[/]", id="approval-desc")

            with Horizontal(id="approval-actions"):
                yield Button("Approve (y)", variant="success", id="approve")
                yield Button("Deny (n)", variant="error", id="deny")

    def action_approve(self) -> None:
        self.dismiss(True)

    def action_deny(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "approve":
            self.action_approve()
        else:
            self.action_deny()
