# JCapy: The One-Army Orchestrator

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

## ✨ Key Features

### 🧠 Autonomous Log Stream Intelligence
**JCapy watches while you work.**
With the new `AutonomousObserver`, JCapy monitors your terminal output in real-time. It detects crash loops, missing dependencies, and runtime errors, instantly offering "Shadow Mode" fixes without you asking.
- **Passive Observation**: No need to copy-paste logs.
- **Shadow Mode**: JCapy privately logs what it *would* have done vs. what you *did*, learning from your expertise.
- **Privacy First**: All data is stored locally in `~/.jcapy/shadow_log.jsonl`.

### 🏗️ One-Army Scaffolding
- **Persona System**: Switch context instantly between `DevOps`, `Frontend`, and `Backend` roles.
- **Framework Harvesting**: Turn any documentation or codebase into a reusable template with `jcapy harvest`.
- **Grade-Aware Deploy**: Deploy with confidence using A/B/C grade pipelines.

### 🛡️ Privacy-First Telemetry
JCapy uses a **"Local-First, Cloud-Optional"** model.
- **Default**: Zero data sent to the cloud.
- **Shadow Logs**: Stored locally in JSONL format for your inspection.
- **Opt-in**: Enable cloud telemetry only if you want to contribute to the global brain.

### 🧩 JCapy Skills Registry
Extend JCapy with community-driven skills.
- **Official Registry**: [ponli550/jcapy-skills](https://github.com/ponli550/jcapy-skills)
- **Create Your Own**: Build your own skills using our [Official Template](https://github.com/ponli550/jcapy-skills/tree/main/templates/python-standard).

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
