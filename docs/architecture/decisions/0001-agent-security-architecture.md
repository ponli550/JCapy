# ADR-0001: Agent Security Architecture

## Status
Accepted

## Context
JCapy needs to securely interact with autonomous agents while preventing unauthorized actions, following OWASP Top 10 for Agentic AI Applications 2026.

## Decision
We implement a multi-layer security architecture:

1. **AgentIdentity (ASI03)**: Every agent has a unique identity with declared permissions
2. **ToolProxy (ASI02, ASI05)**: All tool executions go through a security proxy that validates permissions
3. **CircuitBreaker (ASI08, ASI10)**: Prevents cascading failures and rogue agent behavior
4. **Human-in-the-Loop (ASI02)**: Sensitive operations require explicit approval

## Consequences
- **Positive**: Defense in depth against agent-based attacks
- **Positive**: Audit trail for all agent actions
- **Negative**: Additional complexity in agent operations
- **Negative**: Performance overhead for permission checks

## Implementation
- `src/jcapy/agents/base.py` - AgentIdentity and BaseAgent
- `src/jcapy/agents/security.py` - ToolProxy and CircuitBreaker
- `src/jcapy/core/audit.py` - AuditLogger for action logging