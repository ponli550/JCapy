# JCAPY Super-App Evolution — Technical Design

> **Status:** Phase 2 (In Progress)
> **Goal:** Upgrade JCAPY from a local CLI into a standardized "Nervous System" using MCP, a "Memory" using a Knowledge Lake, and "Logic" using a Knowledge Graph.

---

## 1. Phase 1: The Bridge (MCP Server) [COMPLETED]

The MCP Server acts as the interface between external LLMs (Claude Desktop, NeoVim plugins, etc.) and JCAPY's internal logic.

### 🏗️ Architecture
- **Location**: `src/jcapy/mcp/server.py`
- **Transport**: `stdio` (Standard Input/Output)
- **Framework**: `mcp` Python SDK

### 🛠️ Exposed Tools
1. **`list_skills`**:
   - returns: List of all frameworks in the active persona's library.
   - context: Helps the LLM know what "Executable Knowledge" is available.
2. **`read_skill`**:
   - args: `skill_name`
   - returns: Full content of the skill file.
3. **`apply_skill`**:
   - args: `skill_name`, `dry_run` (bool)
   - returns: Command output or execution status.
   - logic: Wraps `jcapy.commands.frameworks.apply_framework`.
4. **`brainstorm`**:
   - args: `file_content`, `instruction`
   - returns: Re-factored code/skill draft.
   - logic: Wraps JCAPY's AI refactoring logic.

---

## 2. Phase 2: The Memory (Knowledge Lake) [IN PROGRESS]

A centralized repository for unstructured data, enabling better RAG and explicit knowledge ingestion.

### 🏗️ Architecture
- **Vector DB**: ChromaDB (Local persistence at `~/.jcapy/memory_db`)
- **Embedding Model**: `text-embedding-3-small` (OpenAI) or `models/embedding-001` (Gemini)

### 🆕 Key Features
1. **`jcapy memorize` (The Ingestion Engine)**:
   - **Goal**: Explicitly index the Skill Library, docs, and diverse data sources into the Vector DB.
   - **Why**: Avoids risky "lazy sync" during critical triage moments.
   - **Sources**:
     - Skill Library (`.md` files)
     - Project Documentation (`docs/`)
     - Past "Journal" entries (if applicable)
     - Git Logs (optional, for context)

2. **`jcapy recall` (The Search Engine)**:
   - **Goal**: Retrieve relevant skills and context based on semantic queries.
   - **Logic**: Queries ChromaDB and returns ranked matches.

---

## 3. Phase 3: The Intelligence (One-Army Graph) [PLANNED]

Mapping relationships between entities to enable autonomous diagnosis. This replaces the heavy Neo4j plan with a lightweight, "One-Army" specific graph merged with the Observer.

### 🏗️ Architecture
- **Core Concept**: The Graph maps **Dependencies**, not just static links.
- **Integration**: Merged with `src/jcapy/ui/intelligence.py` (The Observer).
- **Flow**:
    1.  **Observer** detects an error (e.g., "Connection refused").
    2.  **Graph** identifies the dependency chain (e.g., Pod -> Service -> DB).
    3.  **Memory** retrieves the fix for that specific component.

### 🧩 Components
- **The Observer**: Monitors logs and events real-time (Existing `AutonomousObserver`).
- **The Graph**: A lightweight dependency mapper (likely in-memory or simple JSON/SQLite).
    - **Nodes**: `Service`, `Database`, `Config`, `Pod`.
    - **Edges**: `DEPENDS_ON`, `CONNECTS_TO`.
- **The Healer**: Suggests or triggers fixes based on the Graph's root cause analysis.

---

## 🚀 Phased Roadmap

### Phase 1: The Bridge (Target: 2 days) - [DONE]
1. [x] Install `mcp` SDK.
2. [x] Implement `server.py` with the 4 core tools.
3. [x] Configure NeoVim/Claude Desktop to use the `jcapy mcp` command.

### Phase 2: The Memory (Target: 3 days) - [current]
1. [x] Integrate `chromadb`.
2. [x] Implement `jcapy recall` for semantic search.
3. [ ] **Implement `jcapy memorize`**:
    - [ ] CLI command to trigger full ingestion.
    - [ ] Robust file scanning and chunking.
    - [ ] Metadata extraction (title, type, date).

### Phase 3: The Intelligence (Target: 5 days) - [next]
1. [ ] **Refactor `intelligence.py`**:
    - [ ] Integrate a `DependencyGraph` class.
    - [ ] Define Node and Edge types for "One-Army" infra.
2. [ ] **Connect Observer to Graph**:
    - [ ] When Observer sees an error, query the Graph for upstream dependencies.
3. [ ] **Connect Graph to Memory**:
    - [ ] Use the identified root cause node to query `jcapy recall` for fixes.
