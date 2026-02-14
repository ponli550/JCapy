# JCapy Command-Mode Orchestrator Design (Phase 7) ⌨️🚀

**Status:** Validated
**Goal:** Transform the JCapy TUI into a modal "Orchestration Shell" where commands are executed via a Vim-like command bar.

## 🎭 Modal State Engine

JCapy will maintain a global `MODE` state within the TUI:

| Mode | Trigger | Focus | Keybinding Behavior |
| :--- | :--- | :--- | :--- |
| **NORMAL** | `Esc` | Navigation | `hjkl` for movement, `:` for command, `/` for search. |
| **COMMAND** | `:` | Input Bar | Character entry for commands, `Tab` for completion, `Enter` to run. |
| **INSERT** | `/` | Filter Bar | Character entry for fuzzy filtering the list. |

## 📟 The Floating Command Bar

A persistent line at the bottom of the Terminal UI (Line `N-1`):
- Displays the active mode (e.g., `-- NORMAL --`).
- In **COMMAND** mode, it accepts typed strings with a `:` prefix.
- **Tab-Completion**: Matches typed input against the JCapy command registry (e.g., `do[TAB]` -> `doctor`).

## 🧊 Floating Glass Panel (Execution Output)

When a command (e.g., `:doctor`) is executed:
1.  **Capture**: JCapy captures the command output (stdout/stderr).
2.  **Overlay**: A temporary `rich.Table` or `Panel` is rendered *over* the dashboard.
3.  **Dismissal**: Pressing any key closes the overlay and return to the dashboard.

## 🏗️ Technical Architecture Updates

- **`src/jcapy/ui/tui.py`**:
    - Update `main()` loop to handle `MODE` state.
    - Implement a `CommandExecutor` that maps TUI commands to JCapy sub-commands.
    - Add `hjkl` mappings to the input handler.
- **`src/jcapy/ui/ux/command_bar.py`** [NEW]:
    - Logic for rendering the bottom bar and handling text input/completion.

---

## 🎯 Success Criteria
- Navigation using `hjkl` feels as fast as Neovim.
- Running `:doctor` from within the TUI shows the health check without exiting.
- Mode switching is instantaneous and visually clear.
