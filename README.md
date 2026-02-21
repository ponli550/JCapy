# JCapy: The One-Army Orchestrator

> 📋 **Project Status**: See [`MASTER_STATUS.md`](./MASTER_STATUS.md) for current progress and known issues.

![JCapy Logo](https://raw.githubusercontent.com/irfansoftstudio/jcapy/main/docs/assets/logo.png)

[![PyPI version](https://badge.fury.io/py/jcapy.svg)](https://badge.fury.io/py/jcapy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)

> **Build Like a Team of Ten.**

**JCapy** is an **Autonomous Engineer** that lives in your terminal. It transforms solo developers into "One-Army" powerhouses by automating knowledge management, project scaffolding, and intelligent debugging.

---

## 🚀 Why JCapy?

In the modern development landscape, context switching kills productivity. JCapy acts as your **context-aware partner**, handling the heavy lifting of project setup, documentation, and debugging so you can focus on writing code.

- **Stop Debugging Alone**: JCapy watches your terminal logs and proactively suggests fixes.
- **Stop Starting from Scratch**: Harvest existing codebases into reusable templates.
- **Stop Losing Context**: Switch between Frontend, Backend, and DevOps personas instantly.

### 🎭 Cinematic Dashboard (2.0)
**JCapy isn't just a CLI; it's a Knowledge OS.**
Experience the new cinematic TUI with a high-end Glassmorphic aesthetic.
- **Cinematic Startup**: Matrix-inspired crystallization reveal with initialization logs.
- **Persistent Mode HUD**: Real-time tracking of input mode, persona, and role (**Sentinel** vs. **Executor**).
- **Advanced Zen Mode**: One-click focus state that removes all UI chrome for deep work.

### 🧠 Cognitive Split (The Sentinel Architecture)
**JCapy plans before it acts.**
Using the "Project Sentinel" persona, the system separates planning from execution.
- **The Sentinel**: Generates high-level execution plans for user approval.
- **The Executor**: Carries out the plan using sandboxed tools.
- **Event-Driven**: Fully decoupled via a high-throughput **Async Event Bus**.

### 🛡️ Secure Tooling & Sandboxing
**Code execution you can trust.**
All JCapy tools run in isolated environments.
- **Sandbox Providers**: Integrated support for local virtualization and **Docker Sandboxing**.
- **Permission Scoping**: Skills must declare permissions (e.g., `file.write`, `network.access`) before execution.
- **Circuit Breakers**: Automatic protection against agent "hallucination loops" or recursive failures.

### 🧩 JCapy Skills Registry
Formalized registry for manageable agent capabilities.
- **Central Index**: Faster discovery via `registry.yaml`.
- **Dependency Resolving**: Skills can declare and validate dependencies.
- **Official Registry**: [irfansoftstudio/jcapy-skills](https://github.com/irfansoftstudio/jcapy-skills)

---

## 📦 Installation

### Homebrew (macOS/Linux)
The recommended way to install on macOS/Linux.
```bash
brew tap ponli550/jcapy
brew install jcapy
```

### Pipx (Universal - Recommended for Python environments)
If you don't use Homebrew, `pipx` is the best way to install Python CLIs in isolated environments.
```bash
pipx install jcapy --python python3.11
```

### Pip (Standard)
```bash
pip install jcapy
```

---

## ⚡ Quick Start

1.  **Initialize JCapy**:
    ```bash
    jcapy init
    ```

2.  **Harvest a Skill from Documentation**:
    ```bash
    jcapy harvest --doc ./my-docs/
    ```

3.  **Brainstorm a New Feature**:
    ```bash
    jcapy brainstorm "Refactor the authentication module"
    ```

4.  **Activate a Persona**:
    ```bash
    jcapy persona activate DevOps
    ```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
