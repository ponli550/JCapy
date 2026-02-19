# Pinecone Integration Implementation Plan

> [!IMPORTANT]
> I am using the premium `writing-plans` skill to record this implementation.
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate Pinecone as a remote vector store for JCapy's memory system using cloud-based inference for embeddings.

**Architecture:** Hybrid vector store approach where `RemoteMemoryBank` uses the Pinecone Inference API (`llama-text-embed-v2`) to generate embeddings and store metadata-enriched chunks in a serverless index. Includes rate-limiting and backoff logic for free-tier resilience.

**Tech Stack:** Pinecone (Inference API), Python 3.12, JCapy Core.

---

### Task 1: Environment Setup

**Files:**
- Modify: `.env`

**Step 1: Configure Pinecone Credentials**
Ensure `.env` contains:
```bash
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=jcapy
PINECONE_MODEL=llama-text-embed-v2
JCAPY_MEMORY_PROVIDER=remote
```

---

### Task 2: Dependency Management

**Files:**
- Modify: `pyproject.toml` (or equivalent)

**Step 1: Install Pinecone SDK**
Run: `pip install pinecone --break-system-packages`
Expected: `Successfully installed pinecone-...`

---

### Task 3: Remote Memory Implementation

**Files:**
- Modify: `jcapy/src/jcapy/memory/remote.py`

**Step 1: Implement RemoteMemoryBank Class**
- Use `pinecone.inference.embed` for passage and query types.
- Implement sliding window chunking (2000 chars).
- Batch upserts in groups of 50.

**Step 2: Add Resilience**
- Implement exponential backoff for `429` rate limit errors.
- Max retries set to 3.

---

### Task 4: Verification

**Files:**
- Create: `verify_pinecone.py` (Temporary)

**Step 1: Run End-to-End Test**
- Ingest a test file.
- Recall the knowledge and verify accuracy.

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| Ingest | `jcapy memorize --path test.txt` | `☁️ [Remote] Indexed: test.txt (1 chunks)` |
| Recall | `jcapy recall "query"` | `✅ Recall successful. Found: test.txt` |

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-19-pinecone-integration.md`. Two execution options:

1. **Subagent-Driven (this session)** - Fresh subagent per task, review between tasks, fast iteration. Recommended for **One-Army Complex tasks**.

2. **Parallel Session (separate)** - Open new session with `executing-plans`, batch execution with manual checkpoints.

**Which approach?**
