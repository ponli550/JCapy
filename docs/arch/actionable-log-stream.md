# JCAPY Design: Actionable Log Stream & Command Cockpit

> **Status:** Validated Design
> **Goal:** Transform JCapy into a high-efficiency DevOps "Command Cockpit" by bridging the gap between live telemetry and actionable commands.

---

## 1. Dual-Pane TUI Architecture

The user interface is split into two persistent zones:

| Pane | Role | Width |
|---|---|---|
| **The Pilot (Left)** | Command Dispatcher & Persona Library | 30-40% |
| **The Stream (Right)** | Real-time Log Telemetry | 60-70% |

### Key UX Features:
- **Persistence**: Log output remains visible on the right while the user selects new actions on the left.
- **Visual Separation**: A thin vertical border with a status indicator: `[STREAMING]` (Green) or `[PAUSED]` (Yellow).
- **Focus Toggle**: `Tab` or `H/L` to switch focus between Pilot and Stream.

---

## 2. The "One-Two Punch" Control Logic

### Selection Mode (The Precision Strike)
- **Activation**: `[` (tmux-style) freezes the stream buffer.
- **Handoff**:
    - `L` (Live): Opens a **Glass-Box Overlay** for `logs` or `describe`. The stream stays frozen.
    - `R` (Root): Dispatches a destructive action (e.g., `restart`) to the **Pilot** and resumes the stream.
- **Viewport Regex**: Async regex highlighting on the visible viewport only. Highlights IDs, Pod names, and IPs in **Cyan**.

### Quick-Action (The Power Search)
- **Activation**: `Ctrl+G` pops a fuzzy-finder over all actionable strings detected in the last 500 lines.
- **Use Case**: Recovering an ID that flew past without scrolling back.

---

## 3. Technical Requirements

### Log Buffer Management
- **Type**: Circular buffer (`collections.deque`) with a 5000-line limit to protect memory.
- **Transport**: Subprocess output piped through a thread-safe queue to the UI loop.

### Selection Engine
- **Frozen State**: Bit flag `is_paused` prevents the UI from shifting the scroll index while active.
- **Hit Detection**: Coordinates of the cursor in selection mode mapped to the string in the buffer.

### Performance (The "Snap" Standard)
- **Lazy Highlighting**: Regex only runs on `on_scroll` or `on_viewport_change` to ensure <16ms frame times.
- **Handoff Utility**: A internal `jcapy.dispatch` function to bridge TUI selection to CLI execution.

---

## 🚀 Roadmap

1.  **Split Implementation**: Basic `curses` or `rich` layout update.
2.  **Stream Engine**: Concurrent output capturing and basic scrolling.
3.  **Selection & Hooks**: Implementation of the `[` mode and `R/L` dispatcher.
4.  **Fuzzy Search**: Integration of `Ctrl+G` logic.
