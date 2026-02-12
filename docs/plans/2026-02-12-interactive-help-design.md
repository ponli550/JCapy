# JCapy Interactive Help Design (TUI Explorer) 🧊

**Date:** 2026-02-12
**Status:** Validated
**Goal:** Replace the static help text with an interactive, Neovim-inspired TUI explorer.

## 🗄️ Architecture & Components

### 1. HELP_REGISTRY (`src/jcapy/commands/help.py`)
A centralized data structure mapping commands to metadata.
- **Title**: Formatted command name.
- **Usage**: Syntax string.
- **Description**: Deep dive into purpose and context.
- **Pro-Tips**: High-value operator advice.

### 2. Interactive Pager (`src/jcapy/commands/help.py`)
A `rich.live` based loop using `rich.layout`.
- **Sidebar (Left, 1/4)**: Vertical list of command names. Highlighted line tracks the `selected_index`.
- **Content (Right, 3/4)**: A `Panel` displaying the `HELP_REGISTRY` entry for the selected command.

### 3. Dynamic Rendering Loop
- **Live Updates**: The UI re-renders on Every arrow key press (Up/Down).
- **Focus Mode**: Pressing `Enter` shifts interaction to the Content Area (for scrolling long entries).

---

## 🎨 Aesthetic Standards
- **Glass Box Style**: All major units wrapped in `create_glass_panel`.
- **Unified Theme**: Respects `jcapy` color palette (CYAN, MAGENTA, YELLOW).
- **Zero Latency**: Pure Python implementation with no external heavy dependencies.

---

## 🛠️ Tech Stack
- **Primary**: Rich (`Text`, `Panel`, `Layout`, `Live`)
- **Input**: Basic `sys.stdin` non-blocking capture.
- **Logic**: Python 3.11+
