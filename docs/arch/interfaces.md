# JCapy Interfaces: The Dual Mode Architecture

JCapy is designed with a "One-Army" philosophy, requiring two distinct modes of operation: **Rapid Execution** (CLI) and **Deep Management** (TUI).

## 1. The CLI (Command Line Interface)
> **"The Hands"** - Fast, Scriptable, Precise.

The CLI is invoked via `jcapy <command>`. It spins up, executes a single task, and exits correctly.

### Use Cases
- **Scaffolding**: `jcapy init`, `jcapy apply`
- **Automation**: CI/CD pipelines using `jcapy deploy`
- **Quick Queries**: `jcapy search "api pattern"`

### Behavior
- **Stateless**: Each command is a fresh process.
- **Pipe-Friendly**: Outputs JSON or raw text for piping into other tools (`jcapy ls --json | jq ...`).
- **Silent by Default**: Minimal output unless requested.

---

## 2. The TUI (Text User Interface)
> **"The Cockpit"** - Persistent, interactive, Visual.

The TUI is invoked via `jcapy manage`. It takes over the terminal window to provide a persistent dashboard.

### Use Cases
- **Monitoring**: Real-time logs of running services.
- **Exploration**: Browsing the skill library visually.
- **Complex Workflows**: Interactive conflict resolution during merges.
- **Brainstorming**: Chatting with the AI context.

### Behavior
- **Stateful**: Maintains session history and context.
- **Visual**: Uses `curses`/`textual` for windows, scrolling, and mouse interaction.
- **Event-Driven**: Reacts to background events (e.g., "Build Complete").

---

## 3. How They Connect
Both interfaces share the same **Core Logic** (The Brain).

```mermaid
graph TD
    CLI[CLI (jcapy <cmd>)] -->|Calls| Core[JCapy Core Library]
    TUI[TUI (jcapy manage)] -->|Calls| Core

    Core -->|Reads/Writes| DB[(ChromaDB / Config)]
    Core -->|Executes| Sys[System Commands]
```

- **CLI** updates the state (e.g., `jcapy harvest` adds a skill).
- **TUI** reflects that state instantly (the new skill appears in the dashboard).

In the future **Orbital Architecture** (v2.0), both will connect to a shared background daemon (`jcapyd`), allowing the TUI to display the progress of CLI commands in real-time.
