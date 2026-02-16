from datetime import datetime
from typing import Any
from textual.widgets import Static, Button, TextArea, ListView, ListItem, Label, DirectoryTree, RichLog
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, Grid, Container
from textual.app import ComposeResult
from textual.binding import Binding
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import os
import subprocess

# ==========================================
# WIDGET REGISTRY
# ==========================================
class WidgetRegistry:
    _registry = {}
    _metadata = {}

    @classmethod
    def register(cls, name, widget_cls, description="No description", size="flexible"):
        cls._registry[name] = widget_cls
        cls._metadata[name] = {
            "description": description,
            "size": size  # small, large, flexible
        }

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def get_metadata(cls, name):
        return cls._metadata.get(name, {})

    @classmethod
    def get_all(cls):
        return cls._registry

    @classmethod
    def get_all_metadata(cls):
        return cls._metadata

class ClockWidget(Static):
    """Displays current time (Local/UTC)."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.update_clock()

    def update_clock(self) -> None:
        now = datetime.now()
        utc = datetime.utcnow()
        time_str = f"[bold cyan] {now.strftime('%H:%M:%S')}[/]\n [dim]UTC {utc.strftime('%H:%M')}[/]"
        self.update(time_str)

class KanbanTask(ListItem):
    """A focusable task item in the Kanban board."""
    def __init__(self, title: str, status: str) -> None:
        super().__init__()
        self.task_title = title
        self.status = status # 'todo', 'doing', 'done'

    def compose(self) -> ComposeResult:
        yield Label(f"• {self.task_title}")

class KanbanWidget(Widget, can_focus=True):
    """
    Interactive Kanban Board tracking JCapy Progress from task.md.
    """
    BINDINGS = [
        Binding("left,h", "focus_left", "Focus Left", show=False),
        Binding("right,l", "focus_right", "Focus Right", show=False),
        Binding("enter", "move_task_next", "Move Next", show=False),
        Binding("space", "move_task_done", "Move to Done"),
    ]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a list item."""
        self.action_move_task_next()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Label("[bold red]TO DO[/bold red]", classes="col-header"),
                ListView(id="todo-list"),
                id="col-todo", classes="kanban-col"
            ),
            Vertical(
                Label("[bold yellow]DOING[/bold yellow]", classes="col-header"),
                ListView(id="doing-list"),
                id="col-doing", classes="kanban-col"
            ),
            Vertical(
                Label("[bold green]DONE[/bold green]", classes="col-header"),
                ListView(id="done-list"),
                id="col-done", classes="kanban-col"
            )
        )

    def on_mount(self) -> None:
        self.highlighted = False
        self.call_after_refresh(self.update_board)

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("thick", "green" if active else "blue")

    def update_board(self) -> None:
        task_file = "/Users/irfanali/.gemini/antigravity/brain/41e0cc09-b343-4215-b7f5-16b292e29d81/task.md"
        try:
            todo_list = self.query_one("#todo-list", ListView)
            doing_list = self.query_one("#doing-list", ListView)
            done_list = self.query_one("#done-list", ListView)
        except:
            return

        t_idx, d_idx, x_idx = todo_list.index, doing_list.index, done_list.index
        todo_list.clear()
        doing_list.clear()
        done_list.clear()

        if os.path.exists(task_file):
            with open(task_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("- [ ]"):
                        todo_list.append(KanbanTask(line[5:].strip(), "todo"))
                    elif line.startswith("- [/]"):
                        doing_list.append(KanbanTask(line[5:].strip(), "doing"))
                    elif line.startswith("- [x]"):
                        done_list.append(KanbanTask(line[5:].strip(), "done"))

        if t_idx is not None and t_idx < len(todo_list.children): todo_list.index = t_idx
        if d_idx is not None and d_idx < len(doing_list.children): doing_list.index = d_idx
        if x_idx is not None and x_idx < len(done_list.children): done_list.index = x_idx

    def action_focus_left(self) -> None:
        current = self.app.focused
        if current == self.query_one("#doing-list"): self.query_one("#todo-list").focus()
        elif current == self.query_one("#done-list"): self.query_one("#doing-list").focus()
        else: self.query_one("#todo-list").focus()

    def action_focus_right(self) -> None:
        current = self.app.focused
        if current == self.query_one("#todo-list"): self.query_one("#doing-list").focus()
        elif current == self.query_one("#doing-list"): self.query_one("#done-list").focus()
        else: self.query_one("#done-list").focus()

    def action_move_task_next(self) -> None:
        current_list = self.app.focused
        if not isinstance(current_list, ListView) or current_list.index is None: return
        task = current_list.children[current_list.index]
        if not isinstance(task, KanbanTask): return
        if task.status == "todo": self.update_task_status(task.task_title, "- [ ]", "- [/]")
        elif task.status == "doing": self.update_task_status(task.task_title, "- [/]", "- [x]")
        self.update_board()

    def action_move_task_done(self) -> None:
        current_list = self.app.focused
        if not isinstance(current_list, ListView) or current_list.index is None: return
        task = current_list.children[current_list.index]
        if not isinstance(task, KanbanTask) or task.status == "done": return
        old_prefix = "- [ ]" if task.status == "todo" else "- [/]"
        self.update_task_status(task.task_title, old_prefix, "- [x]")
        self.update_board()

    def update_task_status(self, title: str, old_prefix: str, new_prefix: str) -> None:
        task_file = "/Users/irfanali/.gemini/antigravity/brain/41e0cc09-b343-4215-b7f5-16b292e29d81/task.md"
        if not os.path.exists(task_file): return
        with open(task_file, "r") as f: lines = f.readlines()
        new_lines = []
        found = False
        for line in lines:
            if not found and line.strip() == f"{old_prefix} {title}":
                indent = line[:line.find(old_prefix)]
                new_lines.append(f"{indent}{new_prefix} {title}\n")
                found = True
            else: new_lines.append(line)
        with open(task_file, "w") as f: f.writelines(new_lines)

class ProjectStatusWidget(Static):
    """Current Project Info."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.update_status()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.update_status()

    def update_status(self) -> None:
        cwd = os.getcwd()
        project_name = os.path.basename(cwd)
        try:
            branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL).decode().strip()
        except: branch = "Not a git repo"

        content = f"\n[bold magenta]📂 {project_name.upper()}[/]\n"
        content += f"[dim] {branch}[/]\n"
        content += f"[dim] {cwd.replace(os.path.expanduser('~'), '~')}[/]"
        self.update(content)

class MarketplaceItem(ListItem):
    """An installable skill/widget item."""
    def __init__(self, item: Any) -> None:
        super().__init__()
        self.item_data = item
        self.item_name = item.name

    def compose(self) -> ComposeResult:
        with Horizontal():
             status_icon = "● [green]" if self.item_data.installed else "○ [dim]"
             yield Label(f"{status_icon}{self.item_name}[/]")
             yield Label(f" [dim]({self.item_data.type})[/]", classes="item-type")
             if not self.item_data.installed:
                 yield Button("Install", variant="primary", id=f"install-{self.item_name.lower().replace(' ', '-')}")
             else:
                 yield Label(" [italic green]Installed[/]", classes="item-installed")

class MarketplaceWidget(Container, can_focus=True):
    """Available Skills/Tools with real installation flow."""
    def compose(self) -> ComposeResult:
        yield Label("[bold]🛍️  Marketplace[/bold]", classes="col-header")
        yield ListView(id="marketplace-list")

    def on_mount(self) -> None:
        self.highlighted = False
        self.styles.border = ("solid", "cyan")
        self.update_market()

    def update_market(self) -> None:
        from jcapy.core.marketplace import MarketplaceService
        items = MarketplaceService.get_available_items()

        m_list = self.query_one("#marketplace-list", ListView)
        m_list.clear()
        for item in items:
            m_list.append(MarketplaceItem(item))

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("thick", "green" if active else "cyan")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith("install-"):
            try:
                item_widget = event.button.parent.parent
                item_data = item_widget.item_data
                git_url = item_data.git_url

                self.app.notify(f"🚀 Launching installer for {item_data.name}...", severity="information")
                if hasattr(self.app, "run_command"):
                    # Use the actual git URL for installation
                    self.app.run_command(f"jcapy install {git_url}")
            except Exception as e:
                self.app.notify(f"Error launching installer: {e}", severity="error")

class FileExplorerWidget(Static, can_focus=True):
    """Interactive File Explorer with nvim integration."""
    BINDINGS = [
        Binding("o", "open_file", "Open in nvim"),
        Binding("space", "open_file", "Open (Space)", show=False),
        Binding("m", "map_view", "Map View"),
    ]

    def compose(self) -> ComposeResult:
        yield DirectoryTree("./", id="explorer-tree")

    def on_mount(self) -> None:
        self.highlighted = False
        self.styles.height = "100%"
        self.styles.border = ("solid", "blue")
        self.query_one(DirectoryTree).border_title = "📂 Files"

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("thick", "green" if active else "blue")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.open_path(str(event.path))

    def action_open_file(self) -> None:
        tree = self.query_one(DirectoryTree)
        if tree.cursor_node and not tree.cursor_node.data.is_dir:
             self.open_path(str(tree.cursor_node.data.path))

    def open_path(self, path: str) -> None:
        with self.app.suspend():
            subprocess.run(["nvim", path])

    def action_map_view(self) -> None:
        tree = self.query_one(DirectoryTree)
        node = tree.cursor_node
        if node:
            path = str(node.data.path)
            self.app.notify(f"Mapping: {path}")

class ConsoleDrawer(Container):
    """Slide-up Console Drawer for background task logs."""
    def compose(self) -> ComposeResult:
        yield Label("[bold yellow]❯ CONSOLE[/bold yellow]", id="drawer-header")
        yield RichLog(id="drawer-log", highlight=True, wrap=True, markup=True)

    def on_mount(self) -> None:
        self.styles.dock = "bottom"
        self.styles.height = 3
        self.styles.background = "#1a1a1a"
        self.styles.border = ("ascii", "white")
        self.query_one(RichLog).write("[dim]System ready. Type ':shell' for raw terminal access.[/dim]")

    def write(self, message: str) -> None: self.query_one(RichLog).write(message)

    def toggle(self) -> None:
        if self.styles.height.value == 3: self.styles.height = "30vh"
        else: self.styles.height = 3

class GitLogWidget(Static):
    """Scrollable Git Log."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.refresh_content()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh_content()

    def refresh_content(self):
        try:
            log = subprocess.check_output(["git", "log", "-n", "10", "--pretty=format:%h - %s (%cr)"], stderr=subprocess.DEVNULL).decode().strip()
        except: log = "No git history found."
        import re
        log = re.sub(r"^([a-f0-9]+)", r"[yellow]\1[/]", log, flags=re.MULTILINE)
        border = "green" if getattr(self, "highlighted", False) else "white"
        self.update(Panel(log, title="📜 Recent Activity", border_style=border))
        self.styles.overflow_y = "auto"
        self.styles.height = "100%"

class NewsWidget(Static):
    """Tech News Ticker."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.headlines = ["JCapy v4.0.0 RC", "AI Market Growth", "Python 3.14 Boost", "New MCP Standard", "Textual Updates"]
        self.index = 0
        self.refresh_content()
        self.set_interval(5, self.rotate_news)

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh_content()

    def rotate_news(self):
        self.index = (self.index + 1) % len(self.headlines)
        self.refresh_content()

    def refresh_content(self):
        current = self.headlines[self.index]
        nxt = self.headlines[(self.index + 1) % len(self.headlines)]
        content = f"[bold cyan]BREAKING:[/bold cyan] {current}\n\n[dim]Coming up: {nxt}[/dim]"
        border = "green" if getattr(self, "highlighted", False) else "yellow"
        self.update(Panel(content, title="📰 Tech News", border_style=border))

class UsageTrackerWidget(Static):
    """Tracks AI Token Usage."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.refresh_content()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh_content()

    def refresh_content(self):
        content = f"[bold]Session Usage:[/bold]\nInput:  [cyan]12,500[/] toks\nOutput: [green]4,200[/] toks\n----------------\n[bold yellow]Est. Cost: $0.1500[/bold yellow]"
        border = "green" if getattr(self, "highlighted", False) else "magenta"
        self.update(Panel(content, title="💸 AI Budget", border_style=border))

class ScratchpadWidget(Static):
    """Persistent Scratchpad."""
    def compose(self) -> ComposeResult:
        self.text_area = TextArea(id="scratchpad-area")
        self.text_area.show_line_numbers = False
        yield self.text_area

    def on_mount(self) -> None:
        self.highlighted = False
        self.load_notes()
        self.text_area.border_title = "📝 Scratchpad"
        self.refresh_style()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh_style()

    def refresh_style(self):
        border = "green" if getattr(self, "highlighted", False) else "white"
        self.text_area.styles.border = ("solid", border)

    def load_notes(self):
        path = os.path.expanduser("~/.jcapy/scratchpad.txt")
        if os.path.exists(path):
            with open(path, "r") as f: self.text_area.text = f.read()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        path = os.path.expanduser("~/.jcapy/scratchpad.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(self.text_area.text)

class MCPWidget(Static):
    """Active MCP Tools."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.refresh_content()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh_content()

    def refresh_content(self):
        content = "[bold green]Active Servers:[/bold green]\n- filesystem\n- brave-search\n- github\n\n[dim]3 servers connected.[/dim]"
        border = "green" if getattr(self, "highlighted", False) else "yellow"
        self.update(Panel(content, title="🔌 MCP Tools", border_style=border))

# ==========================================
# WIDGET REGISTRATION
# ==========================================
WidgetRegistry.register("Clock", ClockWidget, "Digital Clock (Local/UTC)", "small")
WidgetRegistry.register("Kanban", KanbanWidget, "Live Task Board from task.md", "large")
WidgetRegistry.register("ProjectStatus", ProjectStatusWidget, "Git Branch & Path Info", "small")
WidgetRegistry.register("Marketplace", MarketplaceWidget, "Available JCapy Plugins", "small")
WidgetRegistry.register("MCP", MCPWidget, "Active MCP Server Status", "small")
WidgetRegistry.register("GitLog", GitLogWidget, "Recent Git Commit History", "flexible")
WidgetRegistry.register("News", NewsWidget, "Tech News Headlines", "small")
WidgetRegistry.register("UsageTracker", UsageTrackerWidget, "Session Token Usage & Cost", "small")
WidgetRegistry.register("Scratchpad", ScratchpadWidget, "Persistent Notes Area", "flexible")
WidgetRegistry.register("FileExplorer", FileExplorerWidget, "Interactive Project Browser", "flexible")
WidgetRegistry.register("ConsoleDrawer", ConsoleDrawer, "Slide-up System Logs", "flexible")
