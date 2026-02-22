# JCapy Developer Guide

## Architecture Overview

JCapy follows Domain-Driven Design (DDD) with three layers:

```
┌─────────────────────────────────────────────┐
│                 Interface Layer              │
│     (ui/, commands/) - TUI & CLI            │
├─────────────────────────────────────────────┤
│                 Services Layer              │
│     (services/) - Frameworks, AI, Git       │
├─────────────────────────────────────────────┤
│                   Core Layer                │
│     (core/, agents/) - Business Logic       │
└─────────────────────────────────────────────┘
```

### Key Rules
- **Core** must never import from UI or Commands
- **Services** should be stateless where possible
- **Interface** is the only place for `rich` or `textual` imports

## Project Structure

```
jcapy/
├── src/jcapy/
│   ├── agents/          # Agent implementations
│   │   ├── base.py      # AgentIdentity, BaseAgent
│   │   ├── security.py  # ToolProxy, CircuitBreaker
│   │   ├── sentinel.py  # Planning agent
│   │   └── jcapy_agent.py # Execution agent
│   ├── commands/        # CLI commands
│   ├── core/            # Business logic
│   │   ├── audit.py     # Audit logging
│   │   ├── bus.py       # Event bus
│   │   ├── sandbox.py   # Execution sandbox
│   │   └── skills.py    # Skills registry
│   ├── services/        # External services
│   ├── ui/              # Textual TUI
│   └── utils/           # Utilities
├── tests/               # Test suite
├── docs/                # Documentation
└── pyproject.toml       # Package config
```

## Creating a New Command

1. Create a new file in `src/jcapy/commands/`:

```python
# my_command.py
from jcapy.core.base import CommandBase

class MyCommand(CommandBase):
    """Description of my command."""
    
    name = "mycommand"
    help_text = "What this command does"
    
    def execute(self, args):
        # Your implementation
        return "Result"
```

2. Register in `commands/__init__.py`

3. Add tests in `tests/commands/test_my_command.py`

## Creating a Skill

### Skill Structure

```
my-skill/
├── jcapy.yaml      # Manifest (required)
├── SKILL.md        # Skill instructions
├── README.md       # Documentation
└── metadata.json   # Optional metadata
```

### jcapy.yaml Manifest

```yaml
name: my-skill
version: 1.0.0
description: What this skill does
author: your-name
category: development
permissions:
  - read:files
  - tool:read
dependencies:
  - other-skill
entrypoint: SKILL.md
```

### Permission Scopes

| Scope | Description |
|-------|-------------|
| `read:files` | Read file contents |
| `write:files` | Modify files |
| `tool:read` | Use read tool |
| `tool:write` | Use write tool |
| `tool:execute` | Execute shell commands |
| `tool:grep` | Search files |
| `*` | All permissions |

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/jcapy --cov-report=term-missing

# Specific test file
pytest tests/agents/test_base_agent.py -v
```

### Writing Tests

```python
import pytest
from jcapy.agents import AgentIdentity, BaseAgent

def test_my_feature():
    # Arrange
    identity = AgentIdentity(
        id="test-agent",
        name="Test",
        version="1.0.0",
        permissions=["read:files"]
    )
    
    # Act
    result = agent.can_execute_scope("read:files")
    
    # Assert
    assert result is True
```

## Security Architecture

### Agent Identity

Every agent has an `AgentIdentity` with declared permissions:

```python
identity = AgentIdentity(
    id="agent-001",
    name="MyAgent",
    version="1.0.0",
    permissions=["read:files", "tool:grep"]
)
```

### Tool Proxy

All tool calls go through `ToolProxy`:

```python
proxy = ToolProxy(
    agent=agent,
    allowed_tools=["read", "grep"],
    approval_required_tools={"write"},  # Requires HITL
    approval_callback=my_approval_function
)
```

### Circuit Breaker

Prevents cascading failures:

```python
breaker = CircuitBreaker(failure_threshold=3)
if breaker.can_execute():
    try:
        result = execute_risky_operation()
        breaker.record_success()
    except Exception:
        breaker.record_failure()
```

## Event Bus

The event bus enables decoupled communication:

```python
from jcapy.core.bus import get_event_bus

bus = get_event_bus()

# Subscribe to events
bus.subscribe("AUDIT_LOG", my_handler)

# Publish events
bus.publish("AUDIT_LOG", {"event": "data"})
```

## Code Style

- **Type hints** on all function signatures
- **Docstrings** on all public functions and classes
- **Conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- **Atomic commits**: One feature/fix per commit

## Debugging

### TUI Debug Mode

Press `d` in the TUI to inspect widget layout/styles.

### Logging

```python
import logging
logger = logging.getLogger("jcapy")
logger.setLevel(logging.DEBUG)
```

### Audit Logs

Check `~/.jcapy/audit/` for action history.