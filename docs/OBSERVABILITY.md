# JCapy Observability Guide

JCapy 2.0 introduces a decoupled, event-driven architecture for observability and governance.

## 📡 The Async Event Bus

Core components communicate via a high-throughput `EventBus` implemented in `jcapy.core.bus`. This allows for real-time telemetry without tightly coupling the engine to observability services.

### Key Event Types

| Event Type | Source | Purpose |
|------------|--------|---------|
| `AUDIT_LOG` | `ToolProxy`, `CognitiveOrchestrator` | Security audit trail and session history. |
| `TRACE` | Internal | Low-level execution tracing. |
| `UI_UPDATE` | TUI | Signals for dashboard widget refreshes. |

## 📜 Audit Persistence

The `AuditLogger` subscribing to the `AUDIT_LOG` stream ensures every agent action is recorded for governance.

### Log Format (JSONL)

Logs are stored in `~/.jcapy/audit.jsonl` with the following schema:

```json
{
  "timestamp": "2026-02-20T17:00:00Z",
  "session_id": "uuid-v4",
  "event_type": "TOOL_CALL",
  "agent_id": "sentinel-01",
  "payload": {
    "tool": "ls",
    "args": ["/home/user"]
  },
  "outcome": "SUCCESS"
}
```

## 🛡️ Governance & Circuit Breakers

The observability layer isn't just for logging; it's active.
- **Circuit Breaker**: Monitors for 3+ consecutive failures on a specific tool/agent.
- **Shadow Mode**: Compares agent-predicted outcomes with actual results to detect drift.
