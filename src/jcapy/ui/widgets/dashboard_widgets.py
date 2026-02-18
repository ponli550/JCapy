from datetime import datetime
from typing import Any
from textual.widgets import Static, Button, TextArea, ListView, ListItem, Label, DirectoryTree, RichLog
from textual import work
from jcapy.ui.widgets.kinetic_input import KineticInput
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, Grid, Container
from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import os
import subprocess
from jcapy.config import CONFIG_MANAGER
from jcapy.ui.messages import ConfigUpdated
from jcapy.ui.widgets.ai_agent import AIAgentWidget

# ==========================================
# WIDGET REGISTRY
# ==========================================
class WidgetRegistry:
    _registry = {}
    _metadata = {}

    @classmethod
    def register(cls, name, widget_cls, description="No description", size="flexible", category="Misc"):
        cls._registry[name] = widget_cls
        cls._metadata[name] = {
            "description": description,
            "size": size,  # small, large, flexible
            "category": category
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

    @classmethod
    def discover_external_widgets(cls):
        """Dynamically find and register widgets from external directory."""
        from jcapy.config import CONFIG_MANAGER
        import importlib.util
        import sys

        ext_path = CONFIG_MANAGER.get("ux.external_widgets_path")
        if not ext_path or not os.path.exists(ext_path):
            return

        for filename in os.listdir(ext_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"jcapy.external.{filename[:-3]}"
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(ext_path, filename))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    try:
                        spec.loader.exec_module(module)
                        # Expecting a register_widget() function in the module
                        if hasattr(module, "register_widget"):
                            module.register_widget(cls)
                    except Exception as e:
                        print(f"Failed to load external widget {filename}: {e}")

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
        time_str = f"[bold cyan]󱑎 {now.strftime('%H:%M:%S')}[/] [dim]LCL[/]\n[dim]󱑎 {utc.strftime('%H:%M')} UTC[/]"
        self.update(time_str)

class KanbanTask(ListItem):
    """A focusable task item in the Kanban board."""
    def __init__(self, title: str, status: str) -> None:
        super().__init__()
        self.task_title = title
        self.status = status # 'todo', 'doing', 'done'

    def compose(self) -> ComposeResult:
        # Strip markdown for display
        clean_title = self.task_title.replace("**", "").replace("__", "").replace("`", "")
        # Standardize icons based on keywords
        icon = "•"
        t_low = clean_title.lower()
        if any(w in t_low for w in ["test", "verify"]): icon = "🧪"
        elif any(w in t_low for w in ["refactor", "fix", "debug"]): icon = "🛠️"
        elif any(w in t_low for w in ["feat", "add", "implement"]): icon = "✨"
        elif any(w in t_low for w in ["docs", "requirement", "readme"]): icon = "📝"
        elif any(w in t_low for w in ["ui", "style", "polish", "visual"]): icon = "🎨"

        # Truncate if too long
        if len(clean_title) > 35:
            clean_title = clean_title[:32] + "..."
        yield Label(f"{icon} {clean_title}")

class KanbanWidget(Widget, can_focus=True):
    """
    Interactive Kanban Board tracking JCapy Progress from task.md.
    """
    BINDINGS = [
        Binding("left,h", "focus_left", "Focus Left", show=False),
        Binding("right,l", "focus_right", "Focus Right", show=False),
        Binding("enter", "move_task_next", "Move Next", show=False),
        Binding("space", "move_task_done", "Move to Done"),
        Binding("a", "archive_done", "Archive Done"),
    ]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a list item."""
        self.action_move_task_next()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Label(" TO DO", classes="col-header todo"),
                ListView(id="todo-list"),
                id="col-todo", classes="kanban-col"
            ),
            Vertical(
                Label("󰔟 DOING", classes="col-header doing"),
                ListView(id="doing-list"),
                id="col-doing", classes="kanban-col"
            ),
            Vertical(
                Label("󰗠 DONE", classes="col-header done"),
                ListView(id="done-list"),
                id="col-done", classes="kanban-col"
            )
        )
        with Horizontal(classes="widget-action-bar"):
            yield Button("📦 Archive Done", variant="primary", id="btn-kanban-archive")
            yield Button("➕ New Task", variant="default", id="btn-kanban-new")

    def on_mount(self) -> None:
        self.highlighted = False
        self.call_after_refresh(self.update_board)

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("round", "green" if active else "blue")

    def update_board(self) -> None:
        from jcapy.config import get_ux_preference
        max_tasks = get_ux_preference("max_task_display") or 5
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
                counts = {"todo": 0, "doing": 0, "done": 0}
                for line in f:
                    line = line.strip()
                    status = None
                    if line.startswith("- [ ]"): status = "todo"
                    elif line.startswith("- [/]"): status = "doing"
                    elif line.startswith("- [x]"): status = "done"

                    if status:
                        counts[status] += 1
                        if counts[status] <= max_tasks:
                            list_widget = todo_list if status == "todo" else (doing_list if status == "doing" else done_list)
                            list_widget.append(KanbanTask(line[5:].strip(), status))

                # Add condensation summary if needed
                for status, count in counts.items():
                    if count > max_tasks:
                        list_widget = todo_list if status == "todo" else (doing_list if status == "doing" else done_list)
                        list_widget.append(ListItem(Label(f"[dim]+ {count - max_tasks} more tasks...[/]")))

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

    def action_archive_done(self) -> None:
        self.archive_done_tasks()

    def archive_done_tasks(self) -> None:
        task_file = "/Users/irfanali/.gemini/antigravity/brain/41e0cc09-b343-4215-b7f5-16b292e29d81/task.md"
        if not os.path.exists(task_file): return
        with open(task_file, "r") as f: lines = f.readlines()
        new_lines = []
        archived_count = 0
        for line in lines:
            if line.strip().startswith("- [x]"):
                archived_count += 1
                continue # Skip/Archive
            new_lines.append(line)

        if archived_count > 0:
            with open(task_file, "w") as f: f.writelines(new_lines)
            self.app.notify(f"Archived {archived_count} tasks!")
            self.update_board()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-kanban-archive":
            self.archive_done_tasks()
        elif event.button.id == "btn-kanban-new":
            self.app.run_command("jcapy task add")

class ProjectStatusWidget(Static):
    """Current Project Info."""
    def on_mount(self) -> None:
        self.highlighted = False
        self.update_status()

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.update_status()

    def update_status(self) -> None:
        self.update("[dim]Loading Status...[/]")
        self.fetch_git_info()

    @work(thread=True)
    def fetch_git_info(self) -> None:
        cwd = os.getcwd()
        project_name = os.path.basename(cwd)
        try:
            branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL).decode().strip()
            # Ahead/Behind check
            try:
                ab = subprocess.check_output(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], stderr=subprocess.DEVNULL).decode().strip().split()
                ahead = ab[0] if ab else "0"
                behind = ab[1] if len(ab) > 1 else "0"
                git_meta = f" [cyan]󰊢 {ahead}[/] [magenta]󰊢 {behind}[/]"
            except:
                git_meta = ""

            # Uncommitted changes
            status_out = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode()
            change_count = len(status_out.splitlines())
            if change_count > 0:
                git_meta += f" [yellow]󰄬{change_count}[/]"

        except:
            branch = "Not a git repo"
            git_meta = ""

        # Smart path truncation
        home = os.path.expanduser('~')
        display_path = cwd.replace(home, "~") if cwd.startswith(home) else cwd

        content = f"\n[bold cyan]📂 {project_name.upper()}[/]\n"
        content += f"[dim] {branch}[/]{git_meta}\n"
        content += f"[dim]📍 {display_path}[/]"
        self.app.call_from_thread(self.update, content)

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
        self.styles.border = ("round", "cyan")
        self.update_market()

    def update_market(self) -> None:
        from jcapy.core.marketplace import MarketplaceService
        items = MarketplaceService.get_available_items()

        m_list = self.query_one("#marketplace-list", ListView)
        m_list.clear()

        if not items:
             m_list.append(ListItem(Label("\n[dim]No plugins found.[/dim]\n[dim]Check internet connection.[/dim]")))
        else:
            for item in items:
                m_list.append(MarketplaceItem(item))

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("round", "green" if active else "cyan")

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
        with Horizontal(classes="widget-action-bar"):
            yield Button("💻 Terminal", variant="default", id="btn-open-terminal")
            yield Button("🔍 Find", variant="primary", id="btn-find-files")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open-terminal":
            tree = self.query_one(DirectoryTree)
            path = str(tree.cursor_node.data.path) if tree.cursor_node else "./"
            if os.path.isfile(path): path = os.path.dirname(path)
            self.app.notify(f"Opening terminal in {path}")
            # Logic to open console drawer specialized to path could go here
            self.app.run_command(f"cd {path}")
        elif event.button.id == "btn-find-files":
            self.app.run_command("jcapy search")

    def on_mount(self) -> None:
        self.highlighted = False
        self.styles.height = "100%"
        self.styles.border = ("round", "blue")
        self.query_one(DirectoryTree).border_title = "📂 Files"

    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.styles.border = ("round", "green" if active else "blue")

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
    """Slide-up Command Bar & System Logs."""
    def compose(self) -> ComposeResult:
        with Horizontal(id="drawer-header"):
            yield Label("[bold yellow]❯ CONSOLE[/bold yellow]")
            yield Label("[dim] (Type ':' for palette)[/dim]", id="drawer-hint")
        yield RichLog(id="drawer-log", highlight=True, wrap=True, markup=True)
        yield KineticInput(placeholder="Type commands (supports shell & pipes: 'list | grep persona')...", id="drawer-input")

    def on_mount(self) -> None:
        self.query_one(RichLog).write("[dim]System ready. Quick commands: 'help', 'persona', 'theme'.[/dim]")

    def on_input_submitted(self, event: KineticInput.Submitted) -> None:
        cmd_text = event.value.strip()
        if not cmd_text:
            return

        # Clear input early
        inp = self.query_one(KineticInput)
        inp.value = ""
        inp.refresh_history()

        # Execute through App engine
        if hasattr(self.app, "run_command"):
             # The app will handle logging to both terminal and this drawer
             if hasattr(self.app, "_log_command_to_history"):
                 self.app._log_command_to_history(cmd_text)
             self.app.run_command(cmd_text)

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
        self.update(Panel("[dim]Fetching Log...[/]", title="📜 Recent Activity"))
        self.fetch_log()

    @work(thread=True)
    def fetch_log(self) -> None:
        try:
            log = subprocess.check_output(["git", "log", "-n", "10", "--pretty=format:%h - %s (%cr)"], stderr=subprocess.DEVNULL).decode().strip()
        except: log = "No git history found."
        import re
        log = re.sub(r"^([a-f0-9]+)", r"[yellow]\1[/]", log, flags=re.MULTILINE)
        border = "green" if getattr(self, "highlighted", False) else "white"

        # Action Bar for Git
        self.app.call_from_thread(self.update, Panel(log, title="📜 Recent Activity", border_style=border))

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="git-log-content")
            with Horizontal(classes="widget-action-bar"):
                 yield Button("🚀 Push", variant="success", id="btn-git-push")
                 yield Button("🔄 Sync", variant="primary", id="btn-git-sync")

    def update_content(self):
        self.query_one("#git-log-content").update(Panel("[dim]Loading...[/]", title="📜 Recent Activity"))
        self.fetch_log_content()

    @work(thread=True)
    def fetch_log_content(self) -> None:
        try:
            log = subprocess.check_output(["git", "log", "-n", "10", "--pretty=format:%h - %s (%cr)"], stderr=subprocess.DEVNULL).decode().strip()
        except: log = "No git history found."
        import re
        log = re.sub(r"^([a-f0-9]+)", r"[yellow]\1[/]", log, flags=re.MULTILINE)
        border = "green" if getattr(self, "highlighted", False) else "white"
        self.app.call_from_thread(self.query_one("#git-log-content").update, Panel(log, title="📜 Recent Activity", border_style=border))

    def on_mount(self) -> None:
        self.highlighted = False
        self.update_content()
        self.styles.overflow_y = "auto"
        self.styles.height = "100%"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-git-push":
            self.app.notify("Pushing to remote...")
            self.app.run_command("git push")
        elif event.button.id == "btn-git-sync":
            self.app.notify("Syncing changes...")
            self.app.run_command("jcapy sync")

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
        from jcapy.utils.usage import USAGE_LOG_MANAGER
        summary = USAGE_LOG_MANAGER.get_session_summary()
        total_summary = USAGE_LOG_MANAGER.get_total_summary()

        in_toks = summary["input_tokens"]
        out_toks = summary["output_tokens"]
        cost = summary["cost"]

        session_limit = CONFIG_MANAGER.get("usage.session_limit", 5.0)

        # Sparkline simulation (using historical data if possible, mock for now)
        spark_data = [2, 5, 3, 8, 4, 9, 7, 12, 10, 15]
        bars = " ▂▃▄▅▆▇█"
        sparkline = "".join(bars[min(len(bars)-1, d // 2)] for d in spark_data)

        # Budget Warning
        warning_style = ""
        if cost >= session_limit: warning_style = " [bold red]! OVER BUDGET[/]"
        elif cost >= (session_limit * 0.8): warning_style = " [bold yellow]! NEAR LIMIT[/]"

        content = Text()
        content.append("\n  ", style="bold magenta")
        content.append("AI CONSUMPTION" + warning_style + "\n", style="bold white")
        content.append(f"  {sparkline}\n\n", style="cyan")

        # Session Metrics
        content.append("  [SESSION]\n", style="dim italic")
        content.append("  IN  ", style="dim white")
        content.append(f"{in_toks:>8,}", style="bold cyan")
        content.append(" toks\n", style="dim")
        content.append("  OUT ", style="dim white")
        content.append(f"{out_toks:>8,}", style="bold green")
        content.append(" toks\n", style="dim")

        content.append("\n  ------------------\n", style="dim")
        content.append("  COST:     ", style="dim white")
        content.append(f"${cost:>8.4f}", style="bold yellow")
        content.append("\n  LIMIT:    ", style="dim white")
        content.append(f"${session_limit:>8.2f}", style="dim")

        content.append("\n\n  [LIFETIME]\n", style="dim italic")
        content.append("  TOTAL:    ", style="dim white")
        content.append(f"${total_summary['cost']:>8.2f}", style="bold magenta")

        border = "red" if cost >= session_limit else ("yellow" if cost >= session_limit*0.8 else "blue")
        if getattr(self, "highlighted", False): border = "green"

        self.update(Panel(content, title="Real-time Budget", border_style=border))

    def on_click(self) -> None:
        """Launch BudgetScreen on click."""
        from jcapy.ui.screens.budget_screen import BudgetScreen

        def handle_save(result):
            if result:
                self.refresh_content()
                self.app.notify("Budget rules updated successfully!", severity="information")

        self.app.push_screen(BudgetScreen(), handle_save)

    def on_config_updated(self, message: ConfigUpdated) -> None:
        """Refresh if usage keys change."""
        if message.key.startswith("usage."):
            self.refresh_content()

class ScratchpadWidget(Static, can_focus=True):
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
        content = Text.assemble(
            ("\n 🔌 ", "bold cyan"), ("MCP INFRASTRUCTURE\n\n", "bold white"),
            ("  filesystem     ", "dim"), ("🟢 LIVE\n", "bold green"),
            ("  brave-search   ", "dim"), ("🟢 LIVE\n", "bold green"),
            ("  github         ", "dim"), ("🔴 OFFLINE\n", "bold red"),
            ("\n  3 servers configured", "italic dim")
        )
        border = "green" if getattr(self, "highlighted", False) else "blue"
        self.update(Panel(content, title="Infrastructure", border_style=border))

# ==========================================
# STATUS WIDGET
# ==========================================

class StatusWidget(Static):
    """Displays live system status."""

    status = reactive("🟢 [bold green]Config Synced[/]")

    def on_mount(self):
        self.set_interval(60, self.update_render)
        self.update_render()

    def watch_status(self, val):
        self.update_render()

    def update_render(self):
        from jcapy.config import CONFIG_MANAGER
        persona = CONFIG_MANAGER.get("core.persona", "developer").capitalize()
        # Identity focused HUD component
        self.update(f"{self.status}  [dim]|[/] 👤 [bold cyan]{persona}[/]")

# ==========================================
# WIDGET REGISTRATION
# ==========================================
WidgetRegistry.register("Clock", ClockWidget, "Digital Clock (Local/UTC)", "small", "System")
WidgetRegistry.register("Kanban", KanbanWidget, "Live Task Board from task.md", "large", "Core")
WidgetRegistry.register("ProjectStatus", ProjectStatusWidget, "Git Branch & Path Info", "small", "Core")
WidgetRegistry.register("Marketplace", MarketplaceWidget, "Available JCapy Plugins", "small", "Marketplace")
WidgetRegistry.register("MCP", MCPWidget, "Active MCP Server Status", "small", "Systems")
WidgetRegistry.register("Status", StatusWidget, "System Status Indicator", "small", "System")
WidgetRegistry.register("GitLog", GitLogWidget, "Recent Git Commit History", "flexible", "Dev Tools")
WidgetRegistry.register("News", NewsWidget, "Tech News Headlines", "small", "Insights")
WidgetRegistry.register("UsageTracker", UsageTrackerWidget, "Session Token Usage & Cost", "small", "Insights")
WidgetRegistry.register("Scratchpad", ScratchpadWidget, "Persistent Notes Area", "flexible", "Core")
WidgetRegistry.register("FileExplorer", FileExplorerWidget, "Interactive Project Browser", "flexible", "Dev Tools")
WidgetRegistry.register("ConsoleDrawer", ConsoleDrawer, "Slide-up System Logs", "flexible", "System")
WidgetRegistry.register("AIAgent", AIAgentWidget, "Real-time AI thought & orchestration pulse", "small", "Systems")

# Initial discovery of external extensions
WidgetRegistry.discover_external_widgets()
