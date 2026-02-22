from textual.widgets import Static, ListView, ListItem, Label
from textual.app import ComposeResult
from textual.reactive import reactive
from jcapy.config import get_task_file_path
import os
import re

class TaskItem(ListItem):
    """A formatted item for the task list."""
    def __init__(self, text: str, status: str):
        super().__init__()
        self.text = text
        self.status = status

    def compose(self) -> ComposeResult:
        icon = "○"
        color = "white"
        if self.status == "done":
            icon = "󰄬"
            color = "green"
        elif self.status == "in_progress":
            icon = "󰔟"
            color = "yellow"

        yield Label(f"[{color}]{icon}[/] {self.text}")

class TaskSidebar(Static):
    """
    A persistent sidebar that live-syncs with the project's task.md.
    Provides immediate feedback on agent progress.
    """

    DEFAULT_CSS = """
    TaskSidebar {
        width: 35;
        background: $surface 20%;
        border-left: tall $accent 15%;
        padding: 1;
    }

    #task-list-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        content-align: center middle;
        width: 100%;
        border-bottom: solid $accent 10%;
    }

    ListView {
        background: transparent;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("📋 LIVE TASKS", id="task-list-title")
        yield ListView(id="sidebar-task-list")

    def on_mount(self) -> None:
        self.refresh_tasks()
        self.set_interval(3, self.refresh_tasks)

    def refresh_tasks(self) -> None:
        """Poll task.md for updates and refresh the list."""
        path = get_task_file_path()
        if not os.path.exists(path):
            return

        try:
            with open(path, "r") as f:
                content = f.read()

            tasks = []
            # Optimized regex for parsing [ ], [/], [x]
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("- [ ]"):
                    tasks.append((line[5:].strip(), "todo"))
                elif line.startswith("- [/]"):
                    tasks.append((line[5:].strip(), "in_progress"))
                elif line.startswith("- [x]"):
                    tasks.append((line[5:].strip(), "done"))

            # Only update if changed (simple diff check)
            list_view = self.query_one("#sidebar-task-list", ListView)

            # Rebuild list if needed
            # For simplicity in this TUI, we rebuild.
            # In a high-perf scenario, we'd only update modified items.
            list_view.clear()
            for text, status in tasks:
                list_view.append(TaskItem(text, status))
        except Exception:
            pass # Fail silently during background refresh
