# Interactive Mission Control Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the JCapy Dashboard from a static status monitor into a 100% interactive and actionable workspace.

**Architecture:** Use Textual's focus system and reactive properties to drive interactivity. Pivot from high-level Static widgets to specialized, focusable components (ListView, DirectoryTree) that emit custom messages or trigger JCapy core actions.

**Tech Stack:** Textual TUI Framework (ListView, DirectoryTree, Reactive, Workers), subprocess (for :shell).

---

### Task 1: The Interactive "Mission Control" Kanban

**Files:**
- Modify: `jcapy/src/jcapy/ui/widgets/dashboard_widgets.py`
- Modify: `jcapy/src/jcapy/ui/screens/dashboard.py`

**Step 1: Implement Navigable Kanban**
Refactor `KanbanWidget` from a single `Static` with a `Table` into a focusable container with three `ListView` columns.
```python
# jcapy/src/jcapy/ui/widgets/dashboard_widgets.py

class KanbanTask(ListItem):
    def __init__(self, task_text, status):
        super().__init__()
        self.task_text = task_text
        self.status = status # "todo", "doing", "done"

    def compose(self) -> ComposeResult:
        yield Label(self.task_text)

class KanbanWidget(Static):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ListView(id="todo-list")
            yield ListView(id="doing-list")
            yield ListView(id="done-list")
```

**Step 2: Add Hotkey Actions**
Handle `ListView.Selected` to move tasks between lists and update `task.md` on disk.
```python
# jcapy/src/jcapy/ui/widgets/dashboard_widgets.py

def on_list_view_selected(self, event: ListView.Selected):
    task = event.item
    # Move logic...
```

**Step 3: Update CSS for focus visibility**
```css
/* dashboard.tcss or dashboard.py CSS */
KanbanWidget ListView:focus {
    border: double $accent;
}
```

### Task 2: Interactive Sidebar File Explorer

**Files:**
- Modify: `jcapy/src/jcapy/ui/screens/dashboard.py`

**Step 1: Replace Side Column with DirectoryTree**
```python
from textual.widgets import DirectoryTree

# In DashboardScreen.compose():
with Vertical(id="left-col"):
    yield DirectoryTree(path="./", id="file-tree")
```

**Step 2: Implement File Open (nvim)**
Handle `DirectoryTree.FileSelected` to trigger a system call or `nvim` via suspend.

### Task 3: Interactive Marketplace (One-Click Install)

**Files:**
- Modify: `jcapy/src/jcapy/ui/widgets/dashboard_widgets.py`

**Step 1: Interactive List Items**
Each plugin item becomes a `ListItem` with a button hidden by default, appearing on hover or focus.

### Task 4: Terminal drawer & :shell Integration

**Files:**
- Modify: `jcapy/src/jcapy/ui/screens/dashboard.py`
- Modify: `jcapy/src/jcapy/main.py`

**Step 1: Suspend logic for :shell**
Implement `suspend()` call in App to drop to shell.
```python
async def action_shell(self):
    with self.app.suspend():
        subprocess.run(["zsh"])
```
