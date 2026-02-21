# TUI ↔ Web Control Plane Integration Plan

## Current State Analysis

### What Exists

| Component | Location | Status |
|-----------|----------|--------|
| **Web UI** | `apps/web/` | ✅ React + Tailwind frontend |
| **WebSocket Bridge** | `apps/web/server/bridge.py` | ✅ FastAPI + ZMQ subscriber |
| **HTTP Control Plane** | `src/jcapy/daemon/server.py` | ✅ Health + metrics endpoints |
| **TUI Application** | `src/jcapy/ui/app.py` | ✅ Textual-based terminal UI |
| **Event Bus** | `src/jcapy/core/bus.py` | ✅ Simple in-process pub/sub |
| **Memory/Database** | `src/jcapy/memory/` | ✅ ChromaDB + Pinecone support |

### Critical Gap Identified

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  TUI (TUI)  │────?────▶│   Bridge     │◀────✓────▶│   Web UI    │
│  Textual    │          │  FastAPI     │             │   React     │
│  EventBus   │          │  WebSocket   │             │   Tailwind  │
└─────────────┘          └──────────────┘             └─────────────┘
       │                        ▲
       │                        │
       │     ┌──────────────┐   │
       └────?│   ZMQ PUB    │───┘
             │  :5555       │
             │  (MISSING!)  │
             └──────────────┘
```

**The bridge.py expects ZMQ at `tcp://localhost:5555` but NO ZMQ publisher exists in the codebase!**

---

## Integration Architecture

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JCapy Control Plane                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐                   │
│  │  TUI (TUI)  │────▶│  ZMQ Bridge  │────▶│   Web UI    │                   │
│  │  Textual    │     │  Publisher   │     │   React     │                   │
│  │  Port 8080  │     │  Port 5555   │     │  Port 8080  │                   │
│  └─────────────┘     └──────────────┘     └─────────────┘                   │
│         │                   │                    │                           │
│         │                   ▼                    │                           │
│         │           ┌──────────────┐             │                           │
│         │           │  WebSocket   │─────────────┘                           │
│         │           │  Port 8000   │                                         │
│         │           │  bridge.py   │                                         │
│         │           └──────────────┘                                         │
│         │                   │                                                │
│         ▼                   ▼                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        Event Flow                                       │ │
│  │  TUI Action → EventBus → ZMQPublisher → ZMQ → bridge.py → WS → Web    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: ZMQ Publisher Module
- [ ] Create `src/jcapy/core/zmq_publisher.py`
  - [ ] ZmqPublisher class with PUB socket on port 5555
  - [ ] ZmqRpcServer class with REP socket on port 5556
  - [ ] Integration with EventBus

### Phase 2: Daemon Integration
- [ ] Update `src/jcapy/daemon/server.py`
  - [ ] Start ZMQ publisher on daemon startup
  - [ ] Publish state changes to ZMQ
  - [ ] Handle RPC commands from Web UI

### Phase 3: TUI Integration
- [ ] Update `src/jcapy/ui/app.py`
  - [ ] Subscribe EventBus to ZMQ publisher
  - [ ] Publish TUI events (commands, results, mode changes)
  - [ ] Handle incoming Web UI commands

### Phase 4: Web UI Enhancement
- [ ] Update `apps/web/src/bridgeService.js`
  - [ ] Add command sending capability
  - [ ] Handle approval callbacks
  - [ ] Display real-time TUI state

### Phase 5: Database Integration
- [ ] Verify ChromaDB is running
- [ ] Add WebSocket API for memory queries
- [ ] Create memory dashboard widget

### Phase 6: Testing
- [ ] Test TUI → Web event flow
- [ ] Test Web → TUI command flow
- [ ] Test database connectivity
- [ ] Stress test with multiple clients

---

## Event Types

```python
# TUI → Web Events
EVENTS = {
    "TERMINAL_OUTPUT": "terminal output line",
    "COMMAND_EXECUTED": "command string + result",
    "MODE_CHANGED": "NORMAL|INSERT|VISUAL",
    "PERSONA_CHANGED": "persona name",
    "TASK_STARTED": "task id + details",
    "TASK_COMPLETED": "task id + result",
    "AUDIT_LOG": "security audit event",
    "HEARTBEAT": "daemon alive signal"
}

# Web → TUI Commands
COMMANDS = {
    "EXECUTE_COMMAND": "run command in TUI",
    "APPROVE_ACTION": "approve pending action",
    "SWITCH_PERSONA": "change active persona",
    "REQUEST_STATUS": "get current state"
}
```

---

## Database Status

### Current Implementation
- **ChromaDB**: Local vector store at `~/.jcapy/memory_db`
- **Pinecone**: Optional remote memory (via `JCAPY_MEMORY_PROVIDER=remote`)

### Verification Commands
```bash
# Check if ChromaDB is accessible
python -c "from jcapy.memory import get_memory_bank; m = get_memory_bank(); print(m.client)"

# Check memory stats
python -c "from jcapy.memory import get_memory_bank; m = get_memory_bank(); print(m.collection.count())"
```

---

## Success Criteria

1. ✅ TUI terminal output appears in Web UI in real-time
2. ✅ Web UI can send commands to TUI
3. ✅ Approval gates work bidirectionally
4. ✅ Daemon status visible in Web UI
5. ✅ Memory/database queries work from Web UI
6. ✅ Multiple clients can connect simultaneously

---

## File Changes Summary

| File | Change |
|------|--------|
| `src/jcapy/core/zmq_publisher.py` | **NEW** - ZMQ publisher module |
| `src/jcapy/core/bus.py` | **MODIFY** - Add ZMQ bridge support |
| `src/jcapy/daemon/server.py` | **MODIFY** - Integrate ZMQ publisher |
| `src/jcapy/ui/app.py` | **MODIFY** - Connect to ZMQ |
| `apps/web/src/bridgeService.js` | **MODIFY** - Add command support |
| `apps/web/src/App.standalone.js` | **MODIFY** - Add control widgets |