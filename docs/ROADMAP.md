# JCapy Terminal Roadmap

| Phase | Milestone | Objectives | Status |
| :--- | :--- | :--- | :--- |
| **1** | **Research & Discovery** | Analyze `JCapyApp`, `ConsoleDrawer`, and async command engine. | ✅ Done |
| **2** | **Design & Strategy** | Define UX goals, alignment with "One-Army" standards. | ✅ Done |
| **3** | **Core Enhancements** | Optimize capturing (Real-Time Streaming), status feedback. | ✅ Done |

| **4** | **UX/UI Polish** | Cinematic transitions, Glassmorphism, micro-animations. | ✅ Done |
| **5** | **Advanced Interactivity** | Shell Delegation, Multi-Command Piping, grep, TUI Editor, Neovim RPC. | ✅ Done |
| **6** | **Verification** | Performance audits, rendering fixes, final walkthrough. | ✅ Done |

## Analysis Notes
- **Phase 3 (Partial)**: basic ANSI support exists via `Text.from_ansi`. Capturing is hooked up to `RichLog`. Needs better visual status indicators.
- **Phase 5 (Complete)**: Full command piping implemented. Native `grep`, `edit`, and Smart Neovim integration added.

## Core Priorities
- **Performance**: Zero-latency feel for command outputs.
- **Aesthetics**: High-end "Glassmorphism" consistent with the JCapy brand.
- **Intelligence**: Context-aware terminal suggestions and auto-fixes.

---

## Phase 7: JCapy 2.0 (The Orbital Architecture)

| Sub-Phase | Milestone | Objectives | Status |
| :--- | :--- | :--- | :--- |
| **7.1** | **Foundations** | Service Layer, gRPC/ZMQ Daemon Infrastructure. | ✅ Done |
| **7.2** | **The Split** | Stateless CLI client, migration to daemon-first execution. | ✅ Done |
| **7.3** | **Cloud Memory**| ChromaDB Cloud Integration, managed vector store. | ✅ Done |
| **7.4** | **Security** | mTLS, WASM Sandboxing, Secret Vault. | ✅ Done |
| **7.5** | **Orbital TUI** | Dedicated stateless TUI client for central Brain. | ✅ Done |

👉 **See Full Vision**: [arch/vision_v2.md](arch/vision_v2.md)
