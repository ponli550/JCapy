from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static, Input
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding
from textual import work
import asyncio
import os
import json
import time
import re
import shutil
import subprocess

class AddServerModal(ModalScreen[dict]):
    """Modal dialog to add a new MCP server."""
    CSS = """
    AddServerModal { align: center middle; }
    #modal-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #modal-title { text-style: bold; color: $accent; margin-bottom: 1; }
    Input { margin-bottom: 1; }
    #modal-buttons { align: right middle; height: auto; }
    #modal-buttons Button { margin-left: 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Add New MCP Server", id="modal-title")
            yield Input(placeholder="Server Name (e.g., filesystem)", id="name-input")
            yield Input(placeholder="Command (e.g., npx ...)", id="cmd-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Add", variant="success", id="add")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            name = self.query_one("#name-input", Input).value.strip()
            cmd = self.query_one("#cmd-input", Input).value.strip()
            if not name or not cmd:
                self.app.notify("Name and command required", severity="error")
                return
            self.dismiss({"name": name, "command": cmd, "enabled": True})
        else:
            self.dismiss(None)

class AddProjectModal(ModalScreen[str]):
    """Modal to create a new project/persona."""
    CSS = """
    AddProjectModal { align: center middle; }
    #modal-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #modal-title { text-style: bold; color: $accent; margin-bottom: 1; }
    Input { margin-bottom: 1; }
    #modal-buttons { align: right middle; height: auto; }
    #modal-buttons Button { margin-left: 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Initialize New Project", id="modal-title")
            yield Input(placeholder="Project Name (e.g., jaavis_dev)", id="name-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Initialize", variant="success", id="create")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            name = self.query_one("#name-input", Input).value.strip().lower()
            if name:
                name = re.sub(r'[^a-z0-9_]', '', name)
                self.dismiss(name)
            else:
                self.app.notify("Name is required", severity="error")
        else:
            self.dismiss(None)

class RenameProjectModal(ModalScreen[str]):
    """Modal to rename projects."""
    def __init__(self, old_name: str):
        super().__init__()
        self.old_name = old_name

    CSS = """
    RenameProjectModal { align: center middle; }
    #modal-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #modal-title { text-style: bold; color: $accent; margin-bottom: 1; }
    Input { margin-bottom: 1; }
    #modal-buttons { align: right middle; height: auto; }
    #modal-buttons Button { margin-left: 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label(f"Rename Project: {self.old_name}", id="modal-title")
            yield Input(placeholder="New Name", id="name-input", value=self.old_name)
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Rename", variant="success", id="apply")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            name = self.query_one("#name-input", Input).value.strip().lower()
            if name and name != self.old_name:
                name = re.sub(r'[^a-z0-9_]', '', name)
                self.dismiss(name)
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)

class GitRemoteModal(ModalScreen[str]):
    """Modal for Git remote configuration."""
    CSS = """
    GitRemoteModal { align: center middle; }
    #modal-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #modal-title { text-style: bold; color: $accent; margin-bottom: 1; }
    Input { margin-bottom: 1; }
    #modal-buttons { align: right middle; height: auto; }
    #modal-buttons Button { margin-left: 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Git Remote Configuration", id="modal-title")
            yield Label("Target Repository URL:")
            yield Input(placeholder="https://github.com/user/repo.git", id="url-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Link Remote", variant="success", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            url = self.query_one("#url-input", Input).value.strip()
            if url: self.dismiss(url)
            else: self.app.notify("URL required", severity="error")
        else:
            self.dismiss(None)

class GitCommitModal(ModalScreen[str]):
    """Modal for explicit Git commits."""
    CSS = """
    GitCommitModal { align: center middle; }
    #modal-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #modal-title { text-style: bold; color: $accent; margin-bottom: 1; }
    Input { margin-bottom: 1; }
    #modal-buttons { align: right middle; height: auto; }
    #modal-buttons Button { margin-left: 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Deploy Changes", id="modal-title")
            yield Label("Deployment Message:")
            yield Input(placeholder="Updates and fixes...", id="commit-msg")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Commit", variant="success", id="commit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "commit":
            msg = self.query_one("#commit-msg", Input).value.strip()
            if msg: self.dismiss(msg)
            else: self.app.notify("Message required", severity="error")
        else:
            self.dismiss(None)

class MCPServerItem(ListItem):
    """An MCP server configuration item."""
    def __init__(self, name: str, command: str, enabled: bool = True):
        super().__init__()
        self.server_name = name
        self.command = command
        self.enabled = enabled

    def compose(self) -> ComposeResult:
        label = Label(f"{self.server_name}", classes="item-label")
        if self.enabled: label.add_class("enabled")
        else: label.add_class("disabled")
        yield label

    def on_click(self) -> None:
        # self.app.notify(f"MCP Server: {self.server_name}\nCommand: {self.command}", severity="information")
        pass

class ProjectItem(ListItem):
    """A project/persona entry in the fleet."""
    def __init__(self, name: str, path: str, locked: bool = False, active: bool = False):
        super().__init__()
        self.project_name = name
        self.path = path
        self.locked = locked
        self.is_active = active

    def compose(self) -> ComposeResult:
        lock_icon = " 🔒" if self.locked else ""
        active_tag = " [bold cyan]󰄬[/]" if self.is_active else ""
        label_text = f"{display_project_name(self.project_name)}{lock_icon}{active_tag}"
        yield Label(label_text, id=f"label-{self.project_name}", classes="item-label")

    def on_mount(self) -> None:
        self.fetch_git_status()

    @work(thread=True)
    def fetch_git_status(self) -> None:
        from jcapy.utils.git_lib import get_git_status
        branch = "none"
        try:
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.path, stderr=subprocess.DEVNULL).decode().strip()
        except: pass

        _, pending = get_git_status(self.path)

        status_tag = f" [dim][{branch}][/dim]" if branch != "none" else ""
        dirty_tag = f" [bold warning]({pending})[/]" if pending > 0 else ""

        lock_icon = " 🔒" if self.locked else ""
        active_tag = " [bold cyan]󰄬[/]" if self.is_active else ""
        final_text = f"{display_project_name(self.project_name)}{lock_icon}{active_tag}{status_tag}{dirty_tag}"

        self.app.call_from_thread(self.query_one(Label).update, final_text)

    def on_click(self) -> None:
        # from jcapy.config import load_config
        # config = load_config()
        # remote = config.get("personas", {}).get(self.project_name, {}).get("remote_url", "No Remote")
        # lock_status = "Locked" if self.locked else "Unlocked"
        # self.app.notify(f"Project: {self.project_name}\nRemote: {remote}\nStatus: {lock_status}", severity="information")
        pass

def display_project_name(name: str) -> str:
    return name.capitalize() if name != "programmer" else "Programmer"

class WidgetItem(ListItem):
    """An installed widget item."""
    def __init__(self, name: str, description: str, enabled: bool = True, column: str = ""):
        super().__init__()
        self.widget_name = name
        self.description = description
        self.enabled = enabled
        self.column = column

    def compose(self) -> ComposeResult:
        status = "✓" if self.enabled else "✗"
        col_tag = f" [dim]({self.column[0].upper()})[/dim]" if self.enabled else ""
        yield Label(f"{status} {self.widget_name}{col_tag}", classes="item-label")

    def on_click(self) -> None:
        if self.enabled: self.screen.remove_widget_from_layout(self.widget_name)
        else: self.screen.prompt_for_column(self.widget_name)

class ColumnSelectModal(ModalScreen[str]):
    """Modal to select dashboard column for a widget."""
    CSS = """
    ColumnSelectModal { align: center middle; }
    #col-dialog { width: 60; border: thick $accent; background: $surface; padding: 1 2; }
    #col-buttons { layout: horizontal; height: auto; margin-top: 1; content-align: center middle; }
    #col-buttons Button { margin: 0 1; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="col-dialog"):
            yield Label("Select Dashboard Column", id="col-title")
            with Horizontal(id="col-buttons"):
                yield Button("Left", id="left_col")
                yield Button("Center", id="center_col")
                yield Button("Right", id="right_col")
            yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel": self.dismiss(None)
        else: self.dismiss(event.button.id)

class PluginItem(ListItem):
    """An installed plugin/skill item."""
    def __init__(self, name: str, version: str, path: str):
        super().__init__()
        self.plugin_name = name
        self.version = version
        self.path = path

    def compose(self) -> ComposeResult:
        yield Label(f"📦 {self.plugin_name} [dim]v{self.version}[/dim]", classes="item-label")

    def on_click(self) -> None:
        # self.app.notify(f"Plugin: {self.plugin_name} v{self.version}\nPath: {self.path}", severity="information")
        pass

class ThemeItem(ListItem):
    """A theme selection item."""
    def __init__(self, name: str, focus_colors: dict):
        super().__init__()
        self.theme_name = name
        self.focus_colors = focus_colors

    def compose(self) -> ComposeResult:
        yield Label(f"🎨 {self.theme_name.capitalize()}", classes="item-label")

    def on_focus(self) -> None:
        bg = self.focus_colors.get("accent", "#007acc")
        self.styles.background = f"{bg} 20%"
        self.styles.border = ("round", bg)
        self.query_one(Label).styles.color = bg

    def on_blur(self) -> None:
        self.styles.background = None
        self.styles.border = None
        self.query_one(Label).styles.color = None

    def on_click(self) -> None:
        from jcapy.config import set_ux_preference
        set_ux_preference("theme", self.theme_name)
        self.app.notify(f"Theme '{self.theme_name}' applied!", severity="success")

class ManagementScreen(Screen):
    """Management interface."""
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "switch_to_dashboard", "Dashboard", show=True),
        Binding("escape", "switch_to_dashboard", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("enter", "activate_item", "Select", show=True),
        Binding("delete", "delete_item", "Delete", show=False),
        Binding("e", "edit_item", "Edit", show=False),
        Binding("l", "lock_project", "Lock/Unlock", show=False),
        Binding("s", "git_sync", "Sync (Repo)", show=False),
        Binding("p", "git_push", "Push (Repo)", show=False),
        Binding("c", "git_commit", "Commit", show=False),
        Binding("u", "git_remote", "Update Remote", show=False),
    ]

    CSS = """
    ManagementScreen { background: $background; layout: vertical; }
    #main-grid { layout: grid; grid-size: 4; grid-columns: 1fr 1fr 1fr 1fr; grid-gutter: 1; height: 1fr; padding: 1; }
    .column { height: 100%; padding: 1 2; background: $surface 30%; border: round $accent 20%; margin: 1; }
    .column-header { text-style: bold; color: $accent; background: $accent 8%; padding: 0 1; margin-bottom: 1; border-bottom: double $accent; }
    .section-header { text-style: bold; color: $accent; margin-top: 1; margin-bottom: 0; padding-left: 1; background: $boost 3%; border-left: solid $accent; }
    .column ListView { height: 1fr; border: none; margin-top: 0; background: transparent; }
    .column Button { width: 100%; margin-top: 1; margin-bottom: 0; }
    #project-actions, #project-git-actions, #project-meta-actions { layout: horizontal; height: auto; margin-top: 1; }
    #project-actions Button, #project-git-actions Button, #project-meta-actions Button { width: 1fr; margin: 0 1; }
    .item-label { width: 100%; padding: 0 1; }
    ListItem { height: auto; padding: 0; margin: 0 1; transition: background 200ms; }
    ListItem:hover { background: $accent 10%; }
    ListItem:focus { background: $accent 20%; border: solid $accent; text-style: bold; }
    ListItem.-active { background: $accent 35%; }
    .enabled { color: $success; }
    .disabled { color: $error; }
    #danger-zone { margin-top: 1; padding: 1; border: tall $error 15%; background: $error 5%; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-grid"):
            with Vertical(classes="column", id="project-column"):
                yield Label("🚀 [bold]Projects Ongoing[/bold]", classes="column-header")
                yield ListView(id="project-list")
                with Horizontal(id="project-actions"):
                    yield Button("+ New", variant="success", id="add-project")
                    yield Button("✏️ Rename", variant="default", id="rename-project-btn")
                with Horizontal(id="project-git-actions"):
                    yield Button("🔄 Sync", variant="primary", id="sync-project-btn")
                    yield Button("🚀 Push", variant="primary", id="push-project-btn")
                with Horizontal(id="project-meta-actions"):
                    yield Button("🔒 Lock", variant="default", id="lock-project-btn")
                    yield Button("🗑️ Delete", variant="error", id="delete-project-btn")
            with Vertical(classes="column", id="mcp-column"):
                yield Label("🔌 [bold]MCP Servers[/bold]", classes="column-header")
                yield ListView(id="mcp-list")
                yield Button("+ Add Server", variant="success", id="add-mcp-server")
            with Vertical(classes="column", id="content-column"):
                yield Label("🧩 [bold]Workspace Elements[/bold]", classes="column-header")
                yield Label("Widgets", classes="section-header")
                yield ListView(id="widget-list")
                yield Label("Plugins", classes="section-header")
                yield ListView(id="plugin-list")
                yield Button("+ Install Plugin", variant="success", id="install-plugin")
            with Vertical(classes="column", id="system-column"):
                yield Label("🎨 [bold]App Systems[/bold]", classes="column-header")
                yield Label("Theme Gallery", classes="section-header")
                yield ListView(id="theme-list")
                with Vertical(id="danger-zone"):
                    yield Label("Management", classes="section-header")
                    yield Button("Save Layout", variant="primary", id="save-layout")
                    yield Button("Reset Layout", variant="warning", id="reset-layout")
                    yield Static(id="layout-info")
                yield Button("⬅️ Back to Dashboard", variant="default", id="btn-back")
        yield Footer()

    def on_mount(self) -> None:
        self.load_projects()
        self.load_mcp_servers()
        self.load_widgets()
        self.load_plugins()
        self.load_themes()
        self.load_layout_info()

    def load_projects(self) -> None:
        proj_list = self.query_one("#project-list", ListView)
        proj_list.clear()
        from jcapy.config import load_config
        config = load_config()
        personas = config.get("personas", {})
        current = config.get("current_persona", "programmer")
        keys = ["programmer"] + sorted([k for k in personas.keys() if k != "programmer"])
        for k in keys:
            p_data = personas.get(k, {})
            # We defer git status checks to avoid blocking here, or can make this a worker too if list growing large
            proj_list.append(ProjectItem(name=k, path=p_data.get("path", ""), locked=p_data.get("locked", False), active=(k == current)))

    def load_mcp_servers(self) -> None:
        mcp_list = self.query_one("#mcp-list", ListView)
        mcp_list.clear()
        servers = [MCPServerItem("filesystem", "npx ...", True), MCPServerItem("github", "npx ...", True)]
        for s in servers: mcp_list.append(s)

    def load_widgets(self) -> None:
        widget_list = self.query_one("#widget-list", ListView)
        widget_list.clear()
        from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()
        active_widgets = {w: col for col, ws in layout.items() for w in ws}
        for name, metadata in WidgetRegistry.get_all_metadata().items():
            widget_list.append(WidgetItem(name=name, description=metadata.get("description", ""), enabled=name in active_widgets, column=active_widgets.get(name, "")))

    def load_plugins(self) -> None:
        plugin_list = self.query_one("#plugin-list", ListView)
        plugin_list.clear()
        from jcapy.config import JCAPY_HOME
        skills_dir = os.path.join(JCAPY_HOME, "skills")
        if os.path.exists(skills_dir):
            for item in os.listdir(skills_dir):
                plugin_list.append(PluginItem(item, "1.0.0", os.path.join(skills_dir, item)))

    def load_themes(self) -> None:
        theme_list = self.query_one("#theme-list", ListView)
        theme_list.clear()
        from jcapy.ui.theme import THEMES
        for name, colors in THEMES.items(): theme_list.append(ThemeItem(name, colors))

    def load_layout_info(self) -> None:
        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()
        info = f"L: {len(layout.get('left_col', []))} | C: {len(layout.get('center_col', []))} | R: {len(layout.get('right_col', []))}"
        self.query_one("#layout-info", Static).update(info)

    def action_refresh(self) -> None:
        self.on_mount()
        self.app.notify("Syncing Fleet UI...")

    def action_quit(self) -> None: self.app.exit()

    def action_switch_to_dashboard(self) -> None: self.app.switch_screen("dashboard")

    def action_activate_item(self) -> None:
        if isinstance(self.focused, (MCPServerItem, WidgetItem, PluginItem, ProjectItem)): self.focused.on_click()

    def action_lock_project(self) -> None:
        if isinstance(self.focused, ProjectItem): self.handle_lock_project(self.focused.project_name)

    def action_git_sync(self) -> None:
        if isinstance(self.focused, ProjectItem): self.handle_git_sync(self.focused.project_name)

    def action_git_push(self) -> None:
        if isinstance(self.focused, ProjectItem): self.handle_git_push(self.focused.project_name)

    def action_git_commit(self) -> None:
        if isinstance(self.focused, ProjectItem): self.handle_git_commit(self.focused.project_name)

    def action_git_remote(self) -> None:
        if isinstance(self.focused, ProjectItem):
            self.app.push_screen(GitRemoteModal(), lambda url: self.handle_update_remote(self.focused.project_name, url) if url else None)

    def handle_lock_project(self, name: str) -> None:
        from jcapy.config import load_config, save_config
        config = load_config()
        if name in config["personas"]:
            config["personas"][name]["locked"] = not config["personas"][name].get("locked", False)
            save_config(config)
            self.load_projects()

    def handle_delete_project(self, name: str) -> None:
        if name == "programmer": return
        from jcapy.config import load_config, save_config
        config = load_config()
        if config["personas"].get(name, {}).get("locked"): return
        path = config["personas"][name].get("path")
        if path and os.path.exists(path): shutil.rmtree(path)
        del config["personas"][name]
        if config.get("current_persona") == name: config["current_persona"] = "programmer"
        save_config(config)
        self.load_projects()

    def create_project(self, name: str) -> None:
        from jcapy.config import load_config, save_config, JCAPY_HOME
        config = load_config()
        if name in config["personas"] or name == "programmer": return
        lib_path = os.path.join(JCAPY_HOME, f"library_{name}")
        os.makedirs(lib_path, exist_ok=True)
        config["personas"][name] = {"path": lib_path, "created_at": str(time.time()), "locked": False}
        save_config(config)
        self.load_projects()

    def rename_project(self, old: str, new: str) -> None:
        from jcapy.config import load_config, save_config, JCAPY_HOME
        config = load_config()
        if new in config["personas"]: return
        p_data = config["personas"].pop(old)
        old_path = p_data.get("path")
        new_path = os.path.join(JCAPY_HOME, f"library_{new}")
        if old_path and os.path.exists(old_path):
            os.rename(old_path, new_path)
            p_data["path"] = new_path
        config["personas"][new] = p_data
        if config.get("current_persona") == old: config["current_persona"] = new
        save_config(config)
        self.load_projects()

    def handle_git_sync(self, name: str) -> None:
        self.ensure_project_remote(name, lambda url: self._exec_git_sync(name, url))

    def handle_git_push(self, name: str) -> None:
        # Pushing usually implies an automated commit if dirty, or just push
        self.ensure_project_remote(name, lambda url: self._exec_git_push(name, url))

    def handle_git_commit(self, name: str) -> None:
        def on_commit(msg):
            if msg: self._exec_git_commit(name, msg)
        self.app.push_screen(GitCommitModal(), on_commit)

    def handle_update_remote(self, name: str, url: str) -> None:
        from jcapy.config import load_config, save_config
        config = load_config()
        config["personas"][name]["remote_url"] = url
        save_config(config)
        path = config["personas"][name].get("path")
        if path and os.path.exists(os.path.join(path, ".git")):
            subprocess.run(["git", "remote", "set-url", "origin", url], cwd=path)
        self.app.notify(f"Remote updated for {name}")

    def ensure_project_remote(self, name: str, callback) -> None:
        from jcapy.config import load_config, save_config
        config = load_config()
        remote = config.get("personas", {}).get(name, {}).get("remote_url")
        if remote:
            callback(remote)
        else:
            def on_url(url):
                if url:
                    config["personas"][name]["remote_url"] = url
                    save_config(config)
                    callback(url)
            self.app.push_screen(GitRemoteModal(), on_url)

            self.app.push_screen(GitRemoteModal(), on_url)

    @work(thread=True)
    def _exec_git_sync(self, name: str, url: str) -> None:
        from jcapy.config import load_config
        self.app.call_from_thread(self.app.notify, f"Syncing {name}...", severity="information")
        path = load_config().get("personas", {}).get(name, {}).get("path")
        if not path: return

        try:
            if not os.path.exists(os.path.join(path, ".git")):
                subprocess.run(["git", "init"], cwd=path, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.run(["git", "remote", "add", "origin", url], cwd=path, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            subprocess.run(["git", "stash"], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # Using asyncio subprocess or just thread-blocking subprocess since we are in a thread worker
            res = subprocess.run(["git", "pull", "origin", "main", "--rebase"], cwd=path, capture_output=True, text=True)
            if res.returncode != 0:
                subprocess.run(["git", "pull", "origin", "master", "--rebase"], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            subprocess.run(["git", "stash", "pop"], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            self.app.call_from_thread(self.app.notify, f"Sync complete: {name}", severity="success")
            self.app.call_from_thread(self.load_projects)
        except Exception as e:
            self.app.call_from_thread(self.app.notify, f"Sync failed: {e}", severity="error")

    @work(thread=True)
    def _exec_git_push(self, name: str, url: str) -> None:
        from jcapy.config import load_config
        self.app.call_from_thread(self.app.notify, f"Deploying {name}...", severity="information")
        path = load_config().get("personas", {}).get(name, {}).get("path")
        if not path: return

        try:
            if not os.path.exists(os.path.join(path, ".git")):
                subprocess.run(["git", "init"], cwd=path, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.run(["git", "remote", "add", "origin", url], cwd=path, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            subprocess.run(["git", "add", "."], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", f"Dashboard Push {time.ctime()}"], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            res = subprocess.run(["git", "push", "origin", "main"], cwd=path, capture_output=True, text=True)
            if res.returncode != 0:
                subprocess.run(["git", "push", "origin", "master"], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            self.app.call_from_thread(self.app.notify, f"Deployment complete: {name}", severity="success")
            self.app.call_from_thread(self.load_projects)
        except Exception as e:
            self.app.call_from_thread(self.app.notify, f"Push failed: {e}", severity="error")

    @work(thread=True)
    def _exec_git_commit(self, name: str, msg: str) -> None:
        from jcapy.config import load_config
        self.app.call_from_thread(self.app.notify, f"Committing to {name}...", severity="information")
        path = load_config().get("personas", {}).get(name, {}).get("path")
        if not path or not os.path.exists(os.path.join(path, ".git")): return
        try:
            subprocess.run(["git", "add", "."], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", msg], cwd=path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            self.app.call_from_thread(self.app.notify, f"Committed: {msg}", severity="success")
            self.app.call_from_thread(self.load_projects)
        except Exception as e:
            self.app.call_from_thread(self.app.notify, f"Commit failed: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-back": self.action_switch_to_dashboard()
        elif bid == "add-project": self.app.push_screen(AddProjectModal(), lambda n: self.create_project(n) if n else None)
        elif bid == "rename-project-btn":
            if isinstance(self.focused, ProjectItem) and self.focused.project_name != "programmer":
                self.app.push_screen(RenameProjectModal(self.focused.project_name), lambda n: self.rename_project(self.focused.project_name, n) if n else None)
        elif bid == "lock-project-btn": self.action_lock_project()
        elif bid == "delete-project-btn":
             if isinstance(self.focused, ProjectItem): self.handle_delete_project(self.focused.project_name)
        elif bid == "sync-project-btn": self.action_git_sync()
        elif bid == "push-project-btn": self.action_git_push()
        elif bid == "save-layout": self.save_current_layout()
        elif bid == "reset-layout": self.reset_to_default_layout()

    def prompt_for_column(self, name: str) -> None:
        self.app.push_screen(ColumnSelectModal(), lambda c: self.add_widget_to_layout(name, c) if c else None)

    def add_widget_to_layout(self, name: str, col: str) -> None:
        from jcapy.config import get_dashboard_layout, set_dashboard_layout
        layout = get_dashboard_layout()
        for c in layout:
            if name in layout[c]: layout[c].remove(name)
        if col in layout: layout[col].append(name)
        set_dashboard_layout(layout)
        self.load_widgets()

    def remove_widget_from_layout(self, name: str) -> None:
        from jcapy.config import get_dashboard_layout, set_dashboard_layout
        layout = get_dashboard_layout()
        for c in layout:
            if name in layout[c]: layout[c].remove(name)
        set_dashboard_layout(layout)
        self.load_widgets()

    def save_current_layout(self) -> None:
        from jcapy.config import get_dashboard_layout
        layout = get_dashboard_layout()
        path = os.path.expanduser("~/.jcapy/layouts/saved_layout.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f: json.dump(layout, f)
        self.app.notify("Layout Saved")

    def reset_to_default_layout(self) -> None:
        from jcapy.config import set_dashboard_layout, DEFAULT_LAYOUT
        set_dashboard_layout(DEFAULT_LAYOUT)
        self.load_layout_info()
        self.load_widgets()
        self.app.notify("Layout Reset")
