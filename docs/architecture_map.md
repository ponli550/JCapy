# JCapy Architecture Overview

JCapy is a unified "Knowledge Operating System" designed for the "One-Army" protocol. It bridges CLI and TUI experiences through a shared command engine and a modular extension system.

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph CLIENTS ["Clients (Stateless)"]
        CLI["main.py (CLI)"]
        TUI["ui/app.py (Textual TUI)"]
        WEB["Web Control Plane (Planned)"]
    end

    subgraph BRAIN ["JCapy Brain (Daemon)"]
        SERVICE["core/service.py (Service Layer)"]
        DAEMON["daemon/server.py (jcapyd)"]
        BUS["core/bus.py (Event Bus)"]
        RPC["gRPC/ZeroMQ Interface"]
    end

    subgraph ENGINE ["Shared Engine"]
        REG["core/plugins.py (Registry)"]
        CFG["core/config_manager.py"]
        HIST["core/history.py"]
    end

    subgraph COMMANDS ["Command Frameworks"]
        PROJ["commands/project.py"]
        SKILL["commands/frameworks.py"]
        BRAIN_CMD["commands/brain.py"]
    end

    subgraph BRAIN_LAYER ["Intelligence & Memory"]
        MEM["memory/ (Vector DB)"]
        MCP["mcp/ (System Tools)"]
        UTIL["utils/ai.py"]
    end

    %% Relationships
    CLI --> RPC
    TUI --> RPC
    WEB --> RPC
    RPC --> DAEMON
    DAEMON --> SERVICE
    SERVICE --> REG
    SERVICE --> BUS
    REG --> ENGINE
    SERVICE --> COMMANDS
    COMMANDS --> BRAIN_LAYER
```

## 📋 Core Layers

### 1. Orchestration Layer (Clients)
The stateless entry points for JCapy. `main.py` (CLI) and `JCapyApp` (TUI) now act as thin clients that communicate with the Brain via gRPC and ZeroMQ.

### 2. JCapy Brain (Service Layer)
The `JCapyService` in `service.py` is the central nexus. It orchestrates:
- **Command Dispatch**: Routing requests to the appropriate handlers.
- **Log Virtualization**: Broadcasting real-time output via ZeroMQ.
- **Event Bus**: Async event distribution across the entire system.
- **Daemon Control**: `jcapyd` manages the background lifecycle and gRPC/ZMQ servers.

### 3. Shared Engine
The core discovery and configuration hub.
- **Registration**: Mapping command names to Python functions.
- **Piping**: Unix-style `|` logic between commands.
- **Capturing**: Real-time output streaming from commands to the UI.
- **TUI Routing**: Native mapping of interactive commands to Textual screens.

### 3. Modular Command Frameworks
Commands are decoupled from the core UI.
- **Project**: Management of local scaffolding and deployment.
- **Skills**: The "Knowledge" aspect—harvesting patterns and applying them.
- **Personas**: Identity management and environment isolation.

### 4. UI Design System
Built on Textual, featuring:
- **Glassmorphism**: Layered transparency and dynamic focus effects defined in `styles.tcss`.
- **HUD (Heads-Up Display)**: Real-time system pulse and project status widgets.
- **Dual Terminal**: Side-by-side execution and command history logs.

### 5. Memory & Intelligence
- **Vector Memory**: ChromaDB storage for long-term project context.
- **MCP Server**: Integration with the Model Context Protocol for advanced agentic tool-use.
- **AI Utils**: Provider-agnostic abstraction for Gemini, OpenAI, etc.

## 💾 Persistence
- **Global**: `~/.jcapy/config.json` stores user preferences and the Persona library.
- **Local**: `.jcapyrc` stores project-specific metadata (Grade, Name).
