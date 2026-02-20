# JCapy Native Agentic Security Architecture Implementation Plan

> [!IMPORTANT]
> **Premium Skill Active: writing-plans**
> I am using the `writing-plans` workflow. This document contains comprehensive, bite-sized tasks, designed for zero-context execution using strict TDD, DRY, and frequent commits.

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Evolve JCapy to be "natively agentic" and capable of securely interacting with external autonomous agents (like OpenClaw/Clawdbot) while strictly adhering to the OWASP Top 10 for Agentic AI Applications 2026.

**Architecture:** We will introduce a new `src/jcapy/agents/` package implementing a secure base framework for agents. To counter key OWASP risks (ASI02: Tool Misuse, ASI03: Privilege Abuse, ASI05: RCE, ASI10: Rogue Agents), we will build an `AgentSecurityBoundary`, a context-isolated memory manager, and an automated `CircuitBreaker` that monitors and terminates excessive or anomalous agent actions. We will also build an `OpenClawAdapter` specifically handling untrusted external agent connections.

**Tech Stack:** Python, Pytest, JCapy Core (Personas, MCP, Memory, Plugins).

---

## 🔒 Security Principles Addressed
- **ASI02 Tool Misuse & ASI05 RCE:** Abstracted `ToolProxy` sandbox preventing unauthorized command execution.
- **ASI03 Identity Abuse:** Strict `AgentPersona` capability manifests.
- **ASI06 Context Poisoning:** Hashed memory chains to ensure immutability of context.
- **ASI08/ASI10 Cascading Failures & Rogue Agents:** `CircuitBreaker` monitoring token usage and operation rate limits.

---

### Task 1: Initialize Core Agentic Base & Identity (ASI03)

**Files:**
- Create: `src/jcapy/agents/__init__.py`
- Create: `src/jcapy/agents/base.py`
- Create: `tests/agents/test_base_agent.py`

**Step 1: Write the failing test**

```python
# Create: tests/agents/test_base_agent.py
import pytest
from jcapy.agents.base import BaseAgent, AgentIdentity

def test_agent_identity_enforcement():
    identity = AgentIdentity(name="Clawdbot", allowed_scopes=["read:files", "tool:calculator"])
    agent = BaseAgent(identity=identity)

    assert agent.identity.name == "Clawdbot"
    assert agent.can_execute_scope("read:files") is True
    assert agent.can_execute_scope("write:system") is False
```

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `pytest tests/agents/test_base_agent.py -v` | `E: ModuleNotFoundError: No module named 'jcapy.agents'` |

**Step 3: Write minimal implementation**

```python
# Create: src/jcapy/agents/__init__.py
# (Empty file)

# Create: src/jcapy/agents/base.py
from dataclasses import dataclass
from typing import List

@dataclass
class AgentIdentity:
    name: str
    allowed_scopes: List[str]

class BaseAgent:
    def __init__(self, identity: AgentIdentity):
        self.identity = identity

    def can_execute_scope(self, scope: str) -> bool:
        return scope in self.identity.allowed_scopes
```

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `pytest tests/agents/test_base_agent.py -v` | `1 passed` |

**Step 5: Commit**

```bash
git add tests/agents/ src/jcapy/agents/
git commit -m "feat(agents): create native agent base and identity boundaries for ASI03"
```

---

### Task 2: Implement Secure Tool Proxy Sandbox (ASI02, ASI05)

**Files:**
- Create: `src/jcapy/agents/security.py`
- Create: `tests/agents/test_security_proxy.py`

**Step 1: Write the failing test**

```python
# Create: tests/agents/test_security_proxy.py
import pytest
from jcapy.agents.security import ToolProxy
from jcapy.agents.base import AgentIdentity, BaseAgent

def test_tool_proxy_blocks_unauthorized_tools():
    identity = AgentIdentity(name="ClawWorker", allowed_scopes=["tool:safe_read"])
    agent = BaseAgent(identity=identity)
    proxy = ToolProxy(agent)

    with pytest.raises(PermissionError, match="Agent unauthorized for tool"):
        proxy.execute_tool("dangerous_rm", {"path": "/"})

    assert proxy.execute_tool("safe_read", {"file": "test.txt"}) == "Safely read test.txt"
```

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `pytest tests/agents/test_security_proxy.py -v` | `E: ImportError: cannot import name 'ToolProxy'` |

**Step 3: Write minimal implementation**

```python
# Create: src/jcapy/agents/security.py
from jcapy.agents.base import BaseAgent

class ToolProxy:
    def __init__(self, agent: BaseAgent):
        self.agent = agent

    def execute_tool(self, tool_name: str, parameters: dict) -> str:
        # Check ASI02: Tool Misuse boundary
        if not self.agent.can_execute_scope(f"tool:{tool_name}"):
            raise PermissionError(f"Agent unauthorized for tool: {tool_name}")

        # Mock execution logic for now
        if tool_name == "safe_read":
            return f"Safely read {parameters.get('file')}"

        return "Executed"
```

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `pytest tests/agents/test_security_proxy.py -v` | `1 passed` |

**Step 5: Commit**

```bash
git add tests/agents/test_security_proxy.py src/jcapy/agents/security.py
git commit -m "feat(agents): implement ToolProxy to sanitize tool execution against ASI02/ASI05"
```

---

### Task 3: Develop the Agent Circuit Breaker (ASI08, ASI10)

**Files:**
- Modify: `src/jcapy/agents/security.py:20`
- Create: `tests/agents/test_circuit_breaker.py`

**Step 1: Write the failing test**

```python
# Create: tests/agents/test_circuit_breaker.py
import pytest
from jcapy.agents.security import CircuitBreaker

def test_circuit_breaker_trips_on_excessive_failures():
    breaker = CircuitBreaker(max_failures=3)

    for _ in range(3):
        breaker.record_failure()

    assert breaker.is_tripped() is True

    with pytest.raises(SystemError, match="Agent execution halted: Circuit Breaker tripped"):
        breaker.check_status()
```

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `pytest tests/agents/test_circuit_breaker.py -v` | `E: ImportError: cannot import name 'CircuitBreaker'` |

**Step 3: Write minimal implementation**

```python
# Append to: src/jcapy/agents/security.py

class CircuitBreaker:
    def __init__(self, max_failures: int = 5):
        self.max_failures = max_failures
        self.failures = 0
        self.tripped = False

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.max_failures:
            self.tripped = True

    def is_tripped(self) -> bool:
        return self.tripped

    def check_status(self):
        if self.tripped:
            raise SystemError("Agent execution halted: Circuit Breaker tripped")
```

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `pytest tests/agents/test_circuit_breaker.py -v` | `1 passed` |

**Step 5: Commit**

```bash
git add tests/agents/test_circuit_breaker.py src/jcapy/agents/security.py
git commit -m "feat(agents): implement CircuitBreaker to prevent rogue agents (ASI10)"
```

---

### Task 4: OpenClaw / External Agent Adapter Integration

**Files:**
- Create: `src/jcapy/agents/openclaw_adapter.py`
- Create: `tests/agents/test_openclaw_adapter.py`

**Step 1: Write the failing test**

```python
# Create: tests/agents/test_openclaw_adapter.py
import pytest
from jcapy.agents.openclaw_adapter import OpenClawAdapter
from jcapy.agents.base import AgentIdentity

def test_openclaw_adapter_runs_in_sandbox():
    identity = AgentIdentity(name="Clawdbot_API", allowed_scopes=[])
    adapter = OpenClawAdapter(identity=identity)

    with pytest.raises(PermissionError, match="External agents run in strict sandbox"):
        adapter.request_system_access()
```

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `pytest tests/agents/test_openclaw_adapter.py -v` | `E: ImportError: cannot import name 'OpenClawAdapter'` |

**Step 3: Write minimal implementation**

```python
# Create: src/jcapy/agents/openclaw_adapter.py
from jcapy.agents.base import BaseAgent, AgentIdentity
from jcapy.agents.security import ToolProxy, CircuitBreaker

class OpenClawAdapter(BaseAgent):
    def __init__(self, identity: AgentIdentity):
        super().__init__(identity)
        self.proxy = ToolProxy(self)
        self.breaker = CircuitBreaker(max_failures=1) # Stricter for external agents

    def request_system_access(self):
        # Strict security boundary for third-party agents like OpenClaw
        raise PermissionError("External agents run in strict sandbox")
```

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `pytest tests/agents/test_openclaw_adapter.py -v` | `1 passed` |

**Step 5: Commit**

```bash
git add tests/agents/test_openclaw_adapter.py src/jcapy/agents/openclaw_adapter.py
git commit -m "feat(agents): add OpenClawAdapter sandbox for dealing with external/third-party AI agents"
```

---

### Task 5: UI Bridge for Human-in-the-Loop Interventions (ASI02 Alignment)

**Goal:** Provide a channel for the `ToolProxy` to notify the Web Control Plane when an intervention is required for a sensitive action.

**Files:**
- Modify: `src/jcapy/agents/security.py`
- Modify: `src/jcapy/daemon/server.py` (Assuming Orbital plan)

**Step 1: Update ToolProxy to emit 'await_approval' events**
Modify `execute_tool` to check for a `requires_approval` flag and, if true, emit an event to the daemon's internal event bus instead of executing immediately.

**Step 2: Connect Daemon Event Bus to ZeroMQ/WebSocket Stream**
Ensure the `jcapyd` daemon dispatches these 'await_approval' events to connected Web clients.

**Step 3: Verification**
Verify that a `WRITE_FILE` attempt triggers an event that reaches the log stream with a `pending_approval_id`.

**Step 5: Commit**
```bash
git add src/jcapy/agents/security.py
git commit -m "feat(security): add intervention event hooks for web-based approvals"
```
