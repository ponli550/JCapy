# ADR-0002: Cognitive Orchestration Split

## Status
Accepted

## Context
The original `brain.py` coupled planning and execution, making it difficult to:
- Reason about agent actions before execution
- Implement proper governance and approval workflows
- Scale agent operations independently

## Decision
We separate the cognitive architecture into two distinct layers:

1. **Sentinel (Planner)**: Analyzes requests and generates execution plans without side effects
2. **Executor (JCapyAgent)**: Executes approved plans with proper sandboxing

## Consequences
- **Positive**: Plans can be reviewed before execution
- **Positive**: Better error handling and recovery
- **Positive**: Enables multi-agent collaboration
- **Negative**: Additional abstraction layer
- **Negative**: Requires explicit plan approval workflow

## Implementation
- `src/jcapy/agents/sentinel.py` - Planning and governance
- `src/jcapy/agents/jcapy_agent.py` - Execution
- `src/jcapy/core/orchestration.py` - CognitiveOrchestrator coordinating both