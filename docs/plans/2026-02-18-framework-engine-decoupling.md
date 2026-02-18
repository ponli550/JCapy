# Framework Engine Decoupling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the core logic from `frameworks.py` into a standalone, UI-agnostic service layer (`jcapy.services.frameworks.engine`) to enable multi-platform scalability (CLI/TUI/MCP).

**Architecture:** Service-Oriented. The `FrameworkEngine` will handle data orchestration, delegating parsing to `MetadataParser` implementations and storage to `StorageProvider` abstractions.

**Tech Stack:** Python, Pydantic (Models), Pytest (TDD).

---

### Phase 1: Infrastructure & Core Service

### Task 1: Define Framework Result Models
**Files:**
- Create: `src/jcapy/models/frameworks.py`
- Test: `tests/models/test_framework_models.py`

**Step 1: Write the failing test**
```python
from jcapy.models.frameworks import FrameworkResult, ResultStatus

def test_result_model_instantiation():
    res = FrameworkResult(status=ResultStatus.SUCCESS, message="Saved", path="/tmp/test.md")
    assert res.status == ResultStatus.SUCCESS
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/models/test_framework_models.py`
Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**
```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class FrameworkResult(BaseModel):
    status: ResultStatus
    message: str
    path: Optional[str] = None
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/models/test_framework_models.py`
Expected: `1 passed`

**Step 5: Commit**
```bash
git add src/jcapy/models/frameworks.py tests/models/test_framework_models.py
git commit -m "infra: add framework result models"
```

---

### Task 2: Create FrameworkEngine Base
**Files:**
- Create: `src/jcapy/services/frameworks/engine.py`
- Test: `tests/services/test_framework_engine.py`

**Step 1: Write the failing test**
```python
from jcapy.services.frameworks.engine import FrameworkEngine

def test_engine_initialization():
    engine = FrameworkEngine()
    assert engine is not None
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/services/test_framework_engine.py`
Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**
```python
class FrameworkEngine:
    """Core orchestrator for JCapy Frameworks/Skills."""
    def __init__(self):
        pass
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/services/test_framework_engine.py`
Expected: `1 passed`

**Step 5: Commit**
```bash
git add src/jcapy/services/frameworks/engine.py tests/services/test_framework_engine.py
git commit -m "feat: initialize FrameworkEngine service"
```

---

### Task 3: Migrate Markdown Parser (Pure Logic)
**Files:**
- Create: `src/jcapy/services/frameworks/parsers/markdown.py`
- Test: `tests/services/test_markdown_parser.py`

**Step 1: Write failing test for parsing**
```python
from jcapy.services.frameworks.parsers.markdown import MarkdownParser

def test_markdown_parsing():
    content = "---\\nname: Test\\n---\\n# Skill"
    parser = MarkdownParser()
    meta = parser.parse(content)
    assert meta["name"] == "Test"
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/services/test_markdown_parser.py`

**Step 3: Implement Pure Parser (Migrate from frameworks.py)**
[Copy logic from frameworks.py:parse_markdown_doc and parse_frontmatter]

**Step 4: Run tests**

**Step 5: Commit**
```bash
git add src/jcapy/services/frameworks/parsers/markdown.py tests/services/test_markdown_parser.py
git commit -m "feat: migrate markdown parser to service layer"
```
