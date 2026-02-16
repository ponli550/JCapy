
You are the **jcapy Architect Bot**. Your goal is to **refactor** the provided code into a 2026 "Fortress" Standard skill.

### Core Constraints:
1.  **Idempotency**: Ensure `mkdir`, `cd`, and `cat` operations don't fail if they've already run.
2.  **Pre-flight Checks**: Add logic to verify dependencies (e.g., `command -v kubectl`) before executing.
3.  **Observability**: Use emojis and clear `echo` statements for every major step.
4.  **Modern Patterns**: Use `[[ ]]` for shell tests and ensure all variables are quoted to handle spaces.
5.  **Harvest-Ready**: Maintain the `<!-- jcapy:EXEC -->` anchor and the Markdown structure.

### Output Format:
Return **only** the improved Markdown content. Do not include conversational filler.


--- TARGET CONTEXT ---
# JCapy: The One-Army Orchestrator

![JCapy Logo](https://raw.githubusercontent.com/irfansoftstudio/jcapy/main/docs/assets/logo.png)

> **Build Like a Team of Ten.**

JCapy is an **Autonomous Engineer** that lives in your terminal. It transforms solo developers into "One-Army" powerhouses by automating knowledge management, project scaffolding, and intelligent debugging.

## Features

### 🧠 Autonomous Log Stream Intelligence
**JCapy watches while you work.**
With the new `AutonomousObserver`, JCapy monitors your terminal output in real-time. It detects crash loops, missing dependencies, and runtime errors, instanly offering "Shadow Mode" fixes without you asking.
- **Passive Observation**: No need to copy-paste logs.
- **Shadow Mode**: JCapy privately logs what it *would* have done vs. what you *did*, learning from your expertise.
- **Privacy First**: All data is stored locally in `~/.jcapy/shadow_log.jsonl`.

### 🚀 One-Army Scaffolding
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


## Installation

### Homebrew (macOS/Linux)
```bash
brew tap ponli550/jcapy
brew install jcapy
```

### Pip (Universal)
```bash
pip install jcapy
```

## Quick Start

1. **Initialize**: `jcapy init`
2. **Harvest Skill**: `jcapy harvest --doc ./my-docs/`
3. **Brainstorm**: `jcapy brainstorm "Refactor this module"`

## License
Apache 2.0 - Open Source and Business Friendly.
