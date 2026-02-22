# ADR-0003: Sandbox Execution Environment

## Status
Accepted

## Context
JCapy agents need to execute commands safely without risking the host system. Direct shell execution poses significant security risks.

## Decision
We implement a sandbox abstraction with multiple backends:

1. **LocalSandbox**: Fallback for development, runs on host with warnings
2. **DockerSandbox**: Production-ready isolated execution in containers

## Consequences
- **Positive**: Isolated execution environment
- **Positive**: Consistent behavior across platforms
- **Positive**: Resource limits and cleanup
- **Negative**: Docker dependency for production
- **Negative**: Performance overhead for container startup

## Implementation
- `src/jcapy/core/sandbox.py` - BaseSandbox interface and implementations
- Docker images: `python:3.11-slim` default