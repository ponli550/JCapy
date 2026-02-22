# JCapy Security Guide

## Overview

JCapy implements security following the **OWASP Top 10 for Agentic AI Applications 2026**. This guide covers security architecture, permissions, and best practices.

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    Human-in-the-Loop                        │
│              (Approval for sensitive actions)               │
├─────────────────────────────────────────────────────────────┤
│                      ToolProxy                              │
│           (Permission validation & sandboxing)              │
├─────────────────────────────────────────────────────────────┤
│                   Circuit Breaker                           │
│         (Failure monitoring & rogue agent prevention)       │
├─────────────────────────────────────────────────────────────┤
│                   Agent Identity                            │
│              (Capability declarations)                      │
└─────────────────────────────────────────────────────────────┘
```

## OWASP ASI Compliance

### ASI02: Tool Misuse Prevention

All tool executions go through `ToolProxy`:

```python
from jcapy.agents.security import ToolProxy

proxy = ToolProxy(
    agent=agent,
    allowed_tools=["read", "grep"],
    approval_required_tools={"write", "execute"}
)

# Unauthorized tool → PermissionError
proxy.call_tool("rm", {"path": "/"})  # BLOCKED
```

### ASI03: Agent Identity Enforcement

Every agent has a unique identity with declared permissions:

```python
from jcapy.agents import AgentIdentity

identity = AgentIdentity(
    id="agent-unique-id",
    name="MyAgent",
    version="1.0.0",
    permissions=["read:files", "tool:grep"]
)

# Check capabilities
if agent.can_execute_scope("write:files"):
    # This will fail if not in permissions
    pass
```

### ASI05: Remote Code Execution Prevention

Sandboxed execution prevents direct host access:

```python
from jcapy.core.sandbox import get_sandbox

# Docker sandbox for isolation
sandbox = get_sandbox("docker")
result = sandbox.run_command("ls -la")  # Runs in container
```

### ASI08 & ASI10: Cascading Failures & Rogue Agents

Circuit breaker monitors and stops failing agents:

```python
from jcapy.agents.security import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=3)

# After 3 failures, circuit opens
# Agent is blocked from further execution
```

## Permission System

### Permission Scopes

| Scope | Description | Risk Level |
|-------|-------------|------------|
| `read:files` | Read file contents | Low |
| `write:files` | Modify/create files | Medium |
| `tool:read` | Use read tool | Low |
| `tool:write` | Use write tool | Medium |
| `tool:execute` | Execute shell commands | High |
| `tool:grep` | Search files | Low |
| `*` | All permissions | Critical |

### Declaring Permissions in Skills

```yaml
# jcapy.yaml
name: my-skill
permissions:
  - read:files
  - tool:grep
  # NOT: write:files (principle of least privilege)
```

## Human-in-the-Loop (HITL)

### Requiring Approval

```python
proxy = ToolProxy(
    agent=agent,
    allowed_tools=["read", "write", "execute"],
    approval_required_tools={"write", "execute"},
    approval_callback=lambda tool, args: ask_user(tool, args)
)

# This will trigger approval callback
proxy.call_tool("write", {"path": "/important/file", "content": "data"})
```

### Approval Callback Implementation

```python
def approval_callback(tool_name: str, params: dict) -> bool:
    """Ask user for approval."""
    print(f"Tool: {tool_name}")
    print(f"Parameters: {params}")
    response = input("Approve? [y/N]: ")
    return response.lower() == "y"
```

## Audit Logging

All agent actions are logged:

```python
from jcapy.core.audit import AuditLogger

logger = AuditLogger(session_id="session-001")
logger.log_event(
    event_type="TOOL_CALL",
    agent_id="agent-001",
    payload={"tool": "read", "args": {"path": "/etc/passwd"}},
    outcome="SUCCESS"
)
```

### Audit Log Location

```
~/.jcapy/audit/
├── session-2026-02-20-001.jsonl
├── session-2026-02-20-002.jsonl
└── ...
```

### Audit Log Format

```json
{"timestamp": "2026-02-20T18:00:00Z", "event_type": "TOOL_CALL", "agent_id": "agent-001", "payload": {...}, "outcome": "SUCCESS"}
```

## Sandbox Configuration

### Local Sandbox (Development)

```python
from jcapy.core.sandbox import LocalSandbox

sandbox = LocalSandbox()
# WARNING: Runs directly on host
```

### Docker Sandbox (Production)

```python
from jcapy.core.sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="python:3.11-slim",
    container_name="jcapy-sandbox"
)
# Isolated execution in container
```

### Configuration

```bash
# Environment variable
export JCAPY_SANDBOX=docker

# Or in config
jcapy config set sandbox docker
```

## Security Best Practices

### 1. Principle of Least Privilege

Only grant permissions that are absolutely necessary:

```yaml
# BAD
permissions: ["*"]

# GOOD
permissions:
  - read:files
  - tool:grep
```

### 2. Always Use HITL for Sensitive Operations

```python
approval_required_tools={"write", "execute", "delete"}
```

### 3. Monitor Audit Logs

Regularly review audit logs for suspicious activity:

```bash
cat ~/.jcapy/audit/*.jsonl | grep "FAILURE"
```

### 4. Use Docker in Production

```bash
jcapy config set sandbox docker
```

### 5. Keep Circuit Breaker Thresholds Low

```python
# More sensitive = safer
CircuitBreaker(failure_threshold=3)  # Good
CircuitBreaker(failure_threshold=100)  # Too permissive
```

## Security Checklist

Before deploying JCapy:

- [ ] All agents have explicit permission declarations
- [ ] Sensitive tools require HITL approval
- [ ] Docker sandbox is enabled for production
- [ ] Audit logging is enabled
- [ ] Circuit breaker thresholds are configured
- [ ] Skills are from verified sources
- [ ] API keys are stored in environment variables (not code)

## Incident Response

### If an Agent Goes Rogue

1. **Circuit breaker** should auto-trip
2. Check audit logs for actions taken
3. Revoke agent permissions if needed
4. Review and fix the triggering condition

### Manual Circuit Breaker Reset

```python
breaker.state = CircuitState.CLOSED
breaker.failure_count = 0
```

## Reporting Security Issues

Please report security vulnerabilities to: security@jcapy.dev