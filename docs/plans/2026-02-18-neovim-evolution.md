# JCapy NeoVIM Evolution Implementation Plan

> [!IMPORTANT]
> I am using the premium `writing-plans` skill to architect this evolution.
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform JCapy into a high-performance "Knowledge OS" with NeoVIM-inspired modal editing, composable command grammar, and zero-latency asynchronous orchestration.

**Architecture:** We will implement a global `InputMode` state machine in the `JCapyApp` core. This will intercept raw key events and route them through a `GrammarProcessor` (Normal Mode), an `InputRouter` (Insert Mode), or an `ActionRegistry` (Command Mode). Performance is optimized using Textual's `@work` decorator for non-blocking job control.

**Tech Stack:** Python, Textual, Lua (via `lupa` for scripting), Asyncio.

---

### Task 1: Modal Core Engine & Cursor Sync
**Files:**
- Modify: `jcapy/src/jcapy/ui/app.py`
- Create: `jcapy/src/jcapy/ui/modes.py`

**Step 1: Write the failing test**
```python
def test_mode_and_cursor_sync():
    app = JCapyApp()
    assert app.current_mode == "NORMAL"
    # Verify cursor sync (mock sys.stdout)
    app.toggle_mode("INSERT")
    assert app.current_mode == "INSERT"
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/ui/test_modes.py`
Expected: FAIL (AttributeError)

**Step 3: Write minimal implementation**
- Implement `InputMode` enum in `modes.py`.
- Add `current_mode` property and `set_cursor_shape` helper to `JCapyApp`.
- Emit ANSI DECSUSR sequences (`\x1b[2 q` for Normal, `\x1b[6 q` for Insert).

**Step 4: Run test to verify it passes**
Run: `pytest tests/ui/test_modes.py`
Expected: PASS

**Step 5: Commit**
```bash
git add jcapy/src/jcapy/ui/modes.py jcapy/src/jcapy/ui/app.py
git commit -m "feat: implement modal core engine and cursor synchronization"
```

---

### Task 2: Composable Command Grammar (Verb + Noun)
**Files:**
- Create: `jcapy/src/jcapy/ui/grammar.py`

**Step 1: Define Verb and Noun maps**
Verbs: `d` (delete), `c` (change), `y` (yank), `p` (paste).
Nouns: `w` (word), `l` (line), `p` (paragraph), `b` (block).

**Step 2: Implement "Sequence Matcher"**
Intercept keys like `d`, `w` and execute the combined action on the focused widget.

**Step 3: Test grammar composition**
Verify that `dw` deletes a word in the focused `Static` or `Input` widget.
1. The "Big Three" Default Categories
These are built into the core of Neovim and are available regardless of your config.

Navigation (Normal Mode)

h j k l: Left, Down, Up, Right.

w / b: Forward/Backward by word.

gg / G: Top/Bottom of file.

0 / $: Start/End of line.

Ctrl+u / Ctrl+d: Page Up/Down.

Editing (Normal Mode)

i / a: Insert before/after cursor.

o / O: New line below/above.

x: Delete character.

dd: Delete (cut) line.

yy: Yank (copy) line.

p: Paste.

u / Ctrl+r: Undo / Redo.

Command & System

:w: Save.

:q: Quit.

:wq: Save and Quit.

ESC: Return to Normal Mode (The most important key!).

2. Your Specific Plugin Hotkeys
Based on your configuration, you have several specialized tools installed. These typically use a "Leader" key (often Space). Common defaults for your plugins include:

Plugin	Likely Hotkey / Command	Purpose
Telescope	<leader>ff or <leader>fg	Find files or Live Grep.
ToggleTerm	Ctrl+\ or <leader>tt	Toggle terminal overlay.
Codeium	Alt+] / Alt+[	Cycle through AI suggestions.
Codeium	Tab	Accept AI suggestion.
Render-Markdown	Automatic	Renders MD files visually.
3. How to see YOUR Literal List
Because your setup loads local configs and custom modules (like your JCapy integration), the only way to see the actual list is to ask Neovim directly while it's running.

The "Wall of Text" Method

Run these inside Neovim to see every mapping registered:

:map: Shows every single active hotkey.

:nmap: Shows only Normal mode hotkeys.

:vmap: Shows only Visual mode hotkeys.

The "Searchable" Method (Recommended)

Since you have Telescope installed, use it to search your hotkeys interactively:

Type :Telescope keymaps and press Enter.

Type a keyword (like "find" or "delete") to see which key is assigned to it.

4. The JCapy Special
You have a custom module for JCapy. Depending on how you scripted it, you likely have custom keys mapped to:

Triggering the JCapy persona picker via Telescope.

Opening a JCapy-specific ToggleTerm session.

Note: If you aren't sure where these are defined, run :verbose map <your-leader-key> to see exactly which file created the shortcut.
**Step 4: Commit**
```bash
git add jcapy/src/jcapy/ui/grammar.py
git commit -m "feat: implement composable command grammar"
```

---

### Task 3: The <Leader> Key & Lua Customization
**Files:**
- Modify: `jcapy/src/jcapy/config.py`
- Create: `jcapy/src/jcapy/ui/custom_maps.py`

**Step 1: Implement Leader key interceptor**
Map `Space` to trigger a temporary "Leader Mode".

**Step 2: Integrate `lupa` for Lua hotkeys** (Optional based on environment)
Allow users to define `init.lua` in `~/.jcapy/init.lua` to map leader keys to Python functions.

**Step 3: Commit**
```bash
git add jcapy/src/jcapy/ui/custom_maps.py
git commit -m "feat: implement leader key and lua customization"
```

---

### Task 4: Asynchronous Job Control (Pulse Sync)
**Files:**
- Modify: `jcapy/src/jcapy/ui/app.py`
- Modify: `jcapy/src/jcapy/ui/widgets/dashboard_widgets.py`

**Step 1: Refactor `run_command` to `@work`**
Ensure terminal commands don't block the UI loop, mimicking NeoVIM's async job control.

**Step 2: Implement "Grid Diffing" for large logs**
Optimize how the `ConsoleDrawer` updates its content to reduce CPU overhead.

**Step 3: Commit**
```bash
git commit -m "perf: optimize job control and rendering"
```
