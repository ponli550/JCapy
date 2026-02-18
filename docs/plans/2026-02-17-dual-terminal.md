# Dual Terminal Implementation Plan

> [!IMPORTANT]
> I am using the premium `writing-plans` sub-skill to ensure a robust, TDD-driven implementation of the Dual Terminal feature.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the single-window JCapy terminal into a side-by-side "Dual Terminal" layout with a persistent Command Center.

**Architecture:** Use Textual's `Horizontal` container to split the `#main-container` into a `#output-pane` (70%) and `#input-pane` (30%). The `#input-pane` will host a persistent `Input` widget and a `#history-log`.

**Tech Stack:** Textual (Horizontal, Vertical, RichLog, Input), Vanilla CSS (styles.tcss).

---

### Task 1: UI Structure Refactor
Update `app.py` to use the new side-by-side layout.

**Files:**
- Modify: `jcapy/src/jcapy/ui/app.py`
- Modify: `jcapy/src/jcapy/ui/styles.tcss`

**Step 1: Update `compose` to include split panes**
Replace the single `VerticalScroll` with a `Horizontal` container splitting output and input.

**Step 2: Define CSS for split panes**
Add `#terminal-container`, `#output-pane`, and `#input-pane` styles to `styles.tcss`.

**Step 3: Verification**
Run `python3 -m jcapy` and verify the screen is split.

### Task 2: Input Routing & Logic
Connect the new `Input` widget to the command execution engine.

**Files:**
- Modify: `jcapy/src/jcapy/ui/app.py`

**Step 1: Implement `on_input_submitted`**
Route text from `#term-input` to `self.run_command()`.

**Step 2: Clear input on submit**
Ensure the input field is emptied after a command is launched.

**Step 3: History Logging**
Write submitted commands to `#history-log` for persistent visibility.

### Task 3: UX Polish
Refine focus management and aesthetics.

**Files:**
- Modify: `jcapy/src/jcapy/ui/styles.tcss`
- Modify: `jcapy/src/jcapy/ui/app.py`

**Step 1: Auto-focus input**
Ensure the input field is focused on mount.

**Step 2: Modern Input Styling**
Apply glassmorphism and blueprint borders to the input field.

**Step 3: Final Sweep**
Verify `Ctrl+P` still works and doesn't conflict with the persistent input.
