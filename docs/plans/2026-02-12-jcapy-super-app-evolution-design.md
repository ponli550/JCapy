# JCAPY Super-App Evolution — Technical Design

> **Status:** Draft (Phase 1 Focused)
> **Goal:** Upgrade JCAPY from a local CLI into a standardized "Nervous System" using MCP, a "Memory" using a Knowledge Lake, and "Logic" using a Knowledge Graph.

---

## 1. Phase 1: The Bridge (MCP Server)

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

## 2. Phase 2: The Memory (Knowledge Lake)

A centralized repository for unstructured data, enabling better RAG.

### 🏗️ Architecture
- **Vector DB**: Qdrant (Local Docker or SQLite-based Vector search like `FAISS`)
- **Embedding Model**: `text-embedding-3-small` (OpenAI) or `models/embedding-001` (Gemini)

### 📊 Data Sources
- Existing `.md` skills.
- Project history (`git logs`).
- Documentation harvested from URLs or PDFs.

---

## 3. Phase 3: The Intelligence (Knowledge Graph)

Mapping relationships between heterogeneous entities.

### 🏗️ Architecture
- **Graph DB**: Neo4j (Local)
- **Nodes**: `Persona`, `Skill`, `File`, `Function`, `API_Endpoint`.
- **Edges**: `DEPENDS_ON`, `CALLS`, `IMPLEMENTS`, `AUTHORED_BY`.

---

## 🚀 Phased Roadmap

### Phase 1: The Bridge (Target: 2 days)
1. Install `mcp` SDK.
2. Implement `server.py` with the 4 core tools.
3. Configure NeoVim/Claude Desktop to use the `jcapy mcp` command.

### Phase 2: The Memory (Target: 3 days)
1. Integrate `qdrant-client`.
2. Implement `jcapy ingest` to vectorize the library.
3. Add `jcapy ask` for semantic search across skills.

### Phase 3: The Intelligence (Target: 5 days)
1. Setup Neo4j instance.
2. Implement project parser to map dependencies.
3. Visualize the graph in a TUI pane or web view.
