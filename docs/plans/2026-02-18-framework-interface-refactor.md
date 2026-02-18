# Framework Engine Interface Refactor Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the legacy `harvest` command and TUI screens to use the `FrameworkEngine` service, removing duplicate logic and ensuring architectural consistency.

**Architecture:** View/Interface Layer consumption. CLI and TUI become thin wrappers around the `FrameworkEngine` service.

---

### Phase 5: Interface Refactor

### Task 4: Refactor CLI `harvest` Command
**Files:**
- Modify: `src/jcapy/commands/frameworks.py`
- Test: `tests/commands/test_framework_cli.py`

**Step 1: Update `harvest_framework` to call `FrameworkEngine`**
```python
# Before
parsed = parse_markdown_doc(doc_path)

# After
engine = FrameworkEngine()
result = engine.harvest(doc_path, tui_data=tui_data)
metadata = result.payload
```

**Step 2: Run existing CLI tests**
Run: `PYTHONPATH=src python3 -m pytest tests/commands/test_framework_cli.py` (if exists) or run a manual harvest test.

**Step 3: Commit**
```bash
git add src/jcapy/commands/frameworks.py
git commit -m "refactor: CLI harvest command to use FrameworkEngine"
```

---

### Task 5: Refactor TUI `HarvestScreen`
**Files:**
- Modify: `src/jcapy/ui/screens/harvest.py`

**Step 1: Simplify `submit` logic**
Instead of calling a worker that calls the legacy function, the worker should now call `FrameworkEngine.harvest`.

**Step 2: Verification**
Run TUI and perform a harvest. Verify "Success" screen still appears correctly.

**Step 3: Commit**
```bash
git add src/jcapy/ui/screens/harvest.py
git commit -m "refactor: TUI HarvestScreen to use FrameworkEngine"
```

---

### Task 6: Final Clean-up
**Files:**
- Modify: `src/jcapy/commands/frameworks.py` (Delete `parse_markdown_doc`, `parse_frontmatter`)

**Step 1: Remove dead code**
Delete the old parsing functions once all callers are migrated.

**Step 2: Run full test suite**

**Step 3: Commit**
```bash
git commit -m "cleanup: remove legacy parsing logic from frameworks.py"
```
