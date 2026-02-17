# JCapy 2.0: The Orbital Architecture

To scale JCapy from a powerful local TUI into a true "Command Center" for a 1-man army, we need to decouple the **Interface** (TUI) from the **Intelligence** (Core Logic).

This document outlines the proposed **Orbital Architecture**.

## 0. Current State Assessment (v1.0 Scorecard)

Before embarking on v2.0, we conducted an honest audit of the current v1.0 system.

| Category | Score | Verdict |
| :--- | :--- | :--- |
| **UX & Aesthetics** | **9.5/10** | 💎 **World Class**. The "One-Army" feel, Glassmorphism TUI, and cinematic intro are the project's strongest assets. |
| **Security** | **9.0/10** | 🛡️ **Fortified**. No `shell=True`, strict path escaping, and rigorous input sanitization make it production-safe. |
| **Functionality** | **8.0/10** | 🛠️ **Feature Rich**. The core loop (Harvest → Apply → Deploy) works perfectly. `grep`, `edit`, and `search` are solid. |
| **Architecture** | **7.5/10** | 🏗️ **Strained**. `tui.py` is approaching "God Class" status (~1.2k lines). It manages too much state, necessitating the **Orbital Split**. |

**Overall Score: 8.5/10** (Solid, Production-Ready, with clear room for enterprise scaling).

## 1. Core Concept: Client-Server Split
Currently, JCapy is a monolithic Python application running in a single process. As we scale, this becomes a bottleneck for responsiveness and concurrency.

**Proposed Architecture:**
- **JCapy Core (The Brain)**: A headless, persistent daemon running in the background. It manages state, executes long-running tasks, handles AI inference, and indexes knowledge (KIs).
- **JCapy Terminal (The View)**: A lightweight, stateless TUI client. It connects to the Brain via a high-speed local socket (gRPC / ZeroMQ).

### Benefits
- **Super Fast Startup**: The TUI launches instantly because it only needs to render the UI; the heavy lifting is already running in the daemon.
- **Persistence**: Your "session" lives in the daemon. Close the terminal, open it later—your running tasks, context, and AI memory are preserved.
- **Multi-Client**: You could have multiple terminal windows (or even a web interface) all talking to the same central Brain.

## 2. Component Breakdown

### A. The Brain (Daemon)
- **Event Bus**: An internal pub/sub system for broadcasting events (e.g., "Build Started", "Test Failed", "AI Suggestion Ready").
- **Plugin Host**: A sandbox for running Skills and Extensions. Isolated from the core to prevent crashes.
- **Memory Engine**: Vector database (ChromaDB) management running continuously for real-time indexing.
- **API Server**: gRPC or WebSocket interface for clients.

### B. The Terminal (Client)
- **Renderer**: Pure rendering logic using `curses` (or a GPU-accelerated library like `ratatui` via Rust bindings for maximum performance).
- **Input Handler**: Captures keys/mouse and sends commands to the Brain.
- **Stream Viewer**: Subscribes to log streams from the Brain.

## 3. Technology Stack

- **Inter-Process Communication (IPC)**:
  - **gRPC (Python)**: Strongly typed contracts (Protobuf), excellent for structured commands.
  - **ZeroMQ**: For high-throughput log streaming.
- **State Management**:
  - **SQLite / Redis**: For persistent session state and fast ephemeral caching.
- **Plugin System**:
  - **WASM (WebAssembly)**: Safely run plugins written in *any* language (Rust, Go, TS) with near-native speed.

## 4. The "One-Army" Advantage
This architecture empowers a single developer to act like a team:
1.  **Orchestration**: Fire off a complex deployment via JCapy.
2.  **Disconnect**: Close the terminal and focus on coding.
3.  **Reconnect**: Open JCapy later to see the deployment finished, logs preserved, and AI analysis ready.

## 5. Security: The Digital Fortress

As a "Command Center," JCapy often holds the keys to the kingdom (cloud credentials, SSH keys). Security must be uncompromising.

### A. Zero-Trust IPC
- **mTLS Everywhere**: Communication between the Terminal and Brain is encrypted via Mutual TLS, even on localhost. This prevents malicious local processes from hijacking the session.
- **Socket Permissions**: Unix domain sockets are locked to the user's UID/GID (mode `0600`).

### B. Plugin Sandboxing (WASM)
- **Capability-Based Security**: Plugins must request specific permissions (e.g., `network:read`, `fs:write:/tmp`).
- **Isolation**: Plugins run in a WASM runtime (like Wasmtime), ensuring they cannot crash the Brain or access unauthorized memory.

### C. The Vault
- **Secret Management**: Integrated encrypted vault (using native OS keyrings like Keychain/secret-service) for storing API keys.
- **No Plaintext**: Secrets are never logged or stored in plaintext config files.

### D. Audit Trails
- **Tamper-Evident Logs**: Every command executed by the Brain is cryptographically signed and logged, creating an immutable history of actions for compliance and debugging.

## 6. The Clawdbot Bridge (Integration Plan)

JCapy and Clawdbot are distinct but complementary. JCapy is the **Developer's Hands**; Clawdbot is the **Assistant's Voice**.

### A. Control Mechanism
- **JCapy → Clawdbot**: Implemented as a standard **Skill** (`skills/assistant/clawdbot.md`).
    - `jcapy ask "..."`: Delegates queries to Clawdbot's LLM context.
    - `jcapy remind "..."`: Uses Clawdbot's proactive notification system.
- **Clawdbot → JCapy**:
    - **Remote Trigger**: Clawdbot (via Telegram/Discord) can trigger specific JCapy workflows (e.g., `jcapy deploy`) via SSH/API.

### B. Shared Intelligence
- **Memory Sync**: JCapy's Brain can read Clawdbot's markdown memory to understand personal context (e.g., "User prefers dark mode").
- **MCP Re-use**: JCapy 2.0 can act as an MCP Client, consuming the *same* tools Clawdbot uses (GitHub, Google Drive) without re-implementing them.

## 7. Strategic Analysis: Future Threats & Mitigations

What could kill JCapy? Here are the top threats and our architectural defenses.

### A. The "OS Integration" Threat
**Threat**: Apple Intelligence or Windows Copilot integrates deeply into the terminal, making JCapy redundant.
**Defense**: **Deep Context Awareness**. OS AI is generic; it doesn't know your specific "One-Army" repo structure, your custom deployment scripts, or your team's coding style. JCapy survives by being *hyper-specialized* for your specific workflow/architecture.

### B. The "Complexity Bloat" Threat
**Threat**: JCapy tries to do too much (Chat, Home Automation, Web Browsing) and becomes slow/buggy like other "do-it-all" tools.
**Defense**: **Strict Scope**. The "Clawdbot Bridge" ensures JCapy stays focused on *Execution*. If it's not about code, config, or deployment, JCapy delegates it to Clawdbot. We never build features that don't ship code.

### C. The "Model Lock-in" Threat
**Threat**: Relying on one AI provider (e.g., OpenAI) is risky if they change pricing or privacy terms.
**Defense**: **Model Agnosticism**. The Brain (Daemon) uses an adapter pattern. You can swap the underlying intelligence from GPT-4 to Claude 3.5 or a local LLaMA model running on your own GPU without changing the JCapy interface.

## 8. Roadmap & Timeline

| Phase | Milestone | Estimated Duration | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **1** | **Foundation** | Steps 1-2 | - `ServiceLayer` abstraction covering Process/Memory.<br>- gRPC Protobuf definitions (`jcapy.proto`).<br>- Proof-of-Concept: Echo command via gRPC. |
| **2** | **The Split** | Steps 3-5 | - `jcapyd` (Daemon) entry point implemented.<br>- `jcapy-cli` (Client) capable of connecting to local daemon.<br>- Migration of `ProcessManager` to daemon-side. |
| **3** | **Streaming** | Steps 6-8 | - ZeroMQ/gRPC streaming for real-time logs.<br>- TUI refactor to consume stream instead of local pipes.<br>- **Alpha Release**: Internal dogfooding. |
| **4** | **Brain Upgrade** | Steps 9-12 | - Move `MemoryBank` (ChromaDB) to daemon.<br>- Implement event bus for async AI analysis.<br>- Persistent session state (SQLite). |
| **5** | **Polish & Plugin** | Steps 13-15 | - WASM Plugin Host implementation.<br>- Web Client prototype (optional).<br>- **Beta Release**: Public testing. |

### Migration Strategy
1.  **Stop the World**: Freeze feature dev on legacy JCapy.
2.  **Strangler Fig**: Move one component at a time (first Logging, then Execution, finally Memory) behind the Service Layer.
3.  **Flip the Switch**: Make `jcapy` command launch the client by default.

This evolution transforms JCapy from a tool into a platform.
