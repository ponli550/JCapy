# JCapy + Acontext: Orbital Integration Master Plan

> **Date:** 2026-02-19
> **Status:** Strategic Architecture Document
> **Scope:** Acontext Architecture Comparison, Orbital Evolution, Integration Roadmap

---

## 1. Executive Summary

This document provides a comprehensive analysis of how JCapy can implement Acontext-inspired architecture patterns while leveraging its unique **Orbital Architecture** (v2.0) to create a differentiated "Context Platform" for the one-army developer.

**Key Insight:** JCapy doesn't need to become Acontext. Instead, Orbital enables JCapy to own the **local-first context platform** niche while optionally integrating with Acontext for enterprise observability.

---

## 2. Architecture Comparison Matrix

### 2.1 ASCII Comparison Table

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                    ACONTEXT ARCHITECTURE vs JCAPY IMPLEMENTATION PATH                        │
├────────────────────┬─────────────────────────┬─────────────────────────┬────────────────────┤
│ COMPONENT          │ ACONTEXT (Server)       │ JCAPY (Current)         │ JCAPY PATH         │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ STORAGE LAYER      │                         │                         │                    │
│ ├─ Metadata        │ PostgreSQL              │ Filesystem (os.walk)    │ index.json catalog │
│ ├─ Files/Blobs     │ S3 / Cloud Storage      │ ~/.jcapy/*.md           │ Lakehouse pattern  │
│ ├─ Vector Index    │ Remote Embeddings       │ ChromaDB (local)        │ Pinecone/ChromaDB  │
│ └─ Cache           │ Redis                   │ In-memory dict          │ Redis (daemon)     │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ INTERFACE LAYER    │                         │                         │                    │
│ ├─ Primary UI      │ Web Dashboard (React)   │ TUI (Textual)           │ Hybrid TUI + Web   │
│ ├─ API             │ REST (FastAPI)          │ CLI argparse            │ gRPC + REST        │
│ ├─ Real-time       │ WebSocket               │ Polling                 │ ZeroMQ stream      │
│ └─ SDK             │ Python/JS SDK           │ Direct imports          │ Plugin system      │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ OBSERVATION LAYER  │                         │                         │                    │
│ ├─ Mechanism       │ SDK-based (explicit)    │ AutonomousObserver      │ Daemon + hooks     │
│ ├─ Trajectory      │ Session recordings      │ JSONL shadow logs       │ Lakehouse index    │
│ ├─ Metrics         │ Success rate dashboard  │ Basic logging           │ Telemetry module   │
│ └─ Replay          │ Full session replay     │ Log viewer              │ Time-travel debug  │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ EXECUTION LAYER    │                         │                         │                    │
│ ├─ Task Queue      │ RabbitMQ                │ Synchronous             │ Background worker  │
│ ├─ Sandbox         │ Server-side isolation   │ None                    │ WASM sandbox       │
│ ├─ Plugin Host     │ Server-side registry    │ Local skills/           │ WASM + LuaJIT      │
│ └─ Multi-tenant    │ Yes                     │ No (One-Army)           │ Optional           │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ SECURITY LAYER     │                         │                         │                    │
│ ├─ Auth            │ API Keys / OAuth        │ None (local)            │ mTLS + Vault       │
│ ├─ Secrets         │ Encrypted env vars      │ .env files              │ OS keyring vault   │
│ ├─ Audit           │ Server logs             │ Basic history           │ Signed audit trail │
│ └─ Isolation       │ Container-based         │ Process-level           │ WASM capabilities  │
├────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────┤
│ CONTEXT ENGINE     │                         │                         │                    │
│ ├─ Sessions        │ First-class concept     │ Implicit                │ Explicit sessions  │
│ ├─ Trajectory      │ Structured storage      │ Flat logs               │ Indexed graph      │
│ ├─ Memory          │ Cloud vector DB         │ ChromaDB local          │ Hybrid local/cloud │
│ └─ Skills          │ Server registry         │ Local markdown          │ Lakehouse indexed  │
└────────────────────┴─────────────────────────┴─────────────────────────┴────────────────────┘
```

### 2.2 Terminology Alignment

| Acontext Term | JCapy Equivalent | Migration Action |
|---------------|------------------|------------------|
| Session | (Implicit) | Add `Session` class to daemon |
| Trajectory | Shadow logs | Restructure as indexed trajectory |
| Context | Memory Bank | Rename/refactor to ContextEngine |
| Sandbox | (None) | Implement WASM sandbox |
| Skill | Framework/Skill | Already aligned |

---

## 3. Orbital Architecture: The Strategic Advantage

### 3.1 Before vs After

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORBITAL ARCHITECTURE TRANSFORMATION                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   BEFORE (v1.0 Monolith)          AFTER (v2.0 Orbital)                 │
│   ─────────────────────          ────────────────────────               │
│                                                                         │
│   ┌─────────────────┐            ┌─────────────────┐                   │
│   │                 │            │   jcapy-cli     │ ← Lightweight    │
│   │   Single TUI    │            │   (Client)      │   Instant start  │
│   │   Process       │            └────────┬────────┘                   │
│   │                 │                     │ gRPC/ZeroMQ                │
│   │   - UI Render   │                     ↓                            │
│   │   - State Mgmt  │            ┌─────────────────┐                   │
│   │   - AI Inference│            │   jcapyd        │ ← Persistent     │
│   │   - Memory      │            │   (Daemon)      │   Background     │
│   │   - Execution   │            │                 │                   │
│   │                 │            │   - Event Bus   │                   │
│   └─────────────────┘            │   - Memory      │                   │
│                                  │   - AI Engine   │                   │
│   ❌ Slow startup                │   - Plugin Host │                   │
│   ❌ Session lost on close       │   - Task Queue  │                   │
│   ❌ Single interface only       └─────────────────┘                   │
│                                                                         │
│                                  ✅ Instant startup                     │
│                                  ✅ Session persistence                 │
│                                  ✅ Multi-client support                │
│                                  ✅ Background task execution           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Strategic Positioning Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT PLATFORM POSITIONING                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                    LOCAL-FIRST (Privacy)                                │
│                           ↑                                             │
│                           │                                             │
│    ┌──────────────────────┼──────────────────────┐                     │
│    │                      │                       │                     │
│    │    JCAPY ORBITAL     │    JCAPY v1.0        │                     │
│    │    (Target State)    │    (Current)         │                     │
│    │    ┌───────────┐     │    ┌───────────┐     │                     │
│    │    │ • Daemon  │     │    │ • TUI     │     │                     │
│    │    │ • gRPC    │     │    │ • Local   │     │                     │
│    │    │ • Hybrid  │     │    │ • Sync    │     │                     │
│    │    └───────────┘     │    └───────────┘     │                     │
│    │                      │                       │                     │
│ LOW ◄─────────────────────┼─────────────────────► HIGH                 │
│    │                      │                       │     OBSERVABILITY   │
│    │    ACONTEXT          │    ENTERPRISE         │                     │
│    │    ┌───────────┐     │    ┌───────────┐     │                     │
│    │    │ • Cloud   │     │    │ • Dataiku │     │                     │
│    │    │ • SDK     │     │    │ • Teams   │     │                     │
│    │    │ • Multi-T │     │    │ • SaaS    │     │                     │
│    │    └───────────┘     │    └───────────┘     │                     │
│    │                      │                       │                     │
│    └──────────────────────┼──────────────────────┘                     │
│                           │                                             │
│                           ↓                                             │
│                    CLOUD-FIRST (Scale)                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Key Competitive Advantages

| Advantage | Description | vs Acontext |
|-----------|-------------|-------------|
| **Session Persistence** | Close terminal, return later—state preserved | Acontext requires server connection |
| **Zero-Latency Local** | No network round-trip for context | Acontext has cloud latency |
| **Privacy by Default** | Everything stays local unless opted-in | Acontext is cloud-dependent |
| **Multi-Interface** | TUI, CLI, Web all talk to same Brain | Acontext is web-only |
| **Offline-First** | Full functionality without internet | Acontext requires connectivity |
| **Hybrid Ready** | Can integrate Acontext as backend | Best of both worlds |

---

## 4. Integration Architecture

### 4.1 Option A: JCapy as Acontext Client

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HYBRID: JCAPY AS ACONTEXT CLIENT                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│   │ jcapy-cli   │ ───► │   jcapyd    │ ───► │  Acontext   │            │
│   │ (Local)     │      │  (Daemon)   │      │  (Cloud)    │            │
│   └─────────────┘      └─────────────┘      └─────────────┘            │
│                               │                                         │
│                               ▼                                         │
│                        ┌─────────────┐                                  │
│                        │ ChromaDB    │ ← Fallback if offline           │
│                        │ (Local)     │                                  │
│                        └─────────────┘                                  │
│                                                                         │
│   USE CASE: Enterprise teams wanting local speed + cloud observability │
│                                                                         │
│   BENEFITS:                                                             │
│   • Local-first speed for daily work                                   │
│   • Cloud backup and team sharing                                      │
│   • Enterprise observability dashboard                                 │
│   • Offline fallback ensures no data loss                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Option B: Acontext as JCapy's Orbital Brain

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HYBRID: ACONTEXT AS ORBITAL BRAIN                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│   │ jcapy-cli   │ ───► │   jcapyd    │ ◄──► │  Acontext   │            │
│   │ (Machine A) │      │  (Local)    │      │  (Cloud)    │            │
│   └─────────────┘      └─────────────┘      └─────────────┘            │
│                               ▲                 │                       │
│   ┌─────────────┐            │                 │                       │
│   │ jcapy-cli   │ ───────────┘                 │                       │
│   │ (Machine B) │  ← Sync via Acontext         │                       │
│   └─────────────┘                              │                       │
│                                                                         │
│   USE CASE: Solo dev with multiple machines, shared skill registry     │
│                                                                         │
│   BENEFITS:                                                             │
│   • Skills sync across machines                                        │
│   • Shared memory/knowledge base                                       │
│   • Centralized trajectory history                                     │
│   • No proprietary sync engine needed                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal:** Establish daemon infrastructure and communication protocol.

```python
# jcapy.proto - gRPC Service Definition

syntax = "proto3";

package jcapy;

service JCapyDaemon {
    // Command execution
    rpc Execute(CommandRequest) returns (CommandResponse);
    rpc ExecuteStream(CommandRequest) returns (stream LogEntry);
    
    // Session management
    rpc GetSession(SessionRequest) returns (SessionResponse);
    rpc ListSessions(Empty) returns (SessionList);
    
    // Memory operations
    rpc Recall(RecallRequest) returns (RecallResponse);
    rpc Memorize(MemorizeRequest) returns (MemorizeResponse);
    
    // Health
    rpc Ping(Empty) returns (Pong);
}

message CommandRequest {
    string command = 1;
    repeated string args = 2;
    map<string, string> env = 3;
}

message CommandResponse {
    int32 exit_code = 1;
    string stdout = 2;
    string stderr = 3;
    double duration = 4;
}

message LogEntry {
    int64 timestamp = 1;
    string level = 2;
    string message = 3;
    map<string, string> metadata = 4;
}

message SessionRequest {
    string session_id = 1;
}

message SessionResponse {
    string session_id = 1;
    int64 created_at = 2;
    string working_directory = 3;
    repeated string command_history = 4;
}

message RecallRequest {
    string query = 1;
    int32 n_results = 2;
}

message RecallResponse {
    repeated MemoryHit hits = 1;
}

message MemoryHit {
    string id = 1;
    string content = 2;
    double distance = 3;
    map<string, string> metadata = 4;
}

message MemorizeRequest {
    repeated string paths = 1;
    bool clear_first = 2;
}

message MemorizeResponse {
    int32 added = 1;
    int32 errors = 2;
    int32 skipped = 3;
}

message Empty {}
message Pong {
    string version = 1;
    int64 uptime = 2;
}

message SessionList {
    repeated SessionResponse sessions = 1;
}
```

**Deliverables:**
- [ ] `jcapy.proto` gRPC definitions
- [ ] `jcapyd` daemon entry point (`src/jcapy/daemon/__init__.py`)
- [ ] Basic command execution via gRPC
- [ ] Unit tests for daemon startup/shutdown

### Phase 2: The Split (Week 3-4)

**Goal:** Separate client from daemon, enable real-time streaming.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2 ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   FILE STRUCTURE:                                                       │
│   src/jcapy/                                                            │
│   ├── __init__.py                                                       │
│   ├── __main__.py          # Entry point (dispatches to cli or daemon)  │
│   ├── cli/                 # Lightweight client                         │
│   │   ├── __init__.py                                                   │
│   │   ├── client.py        # gRPC client wrapper                        │
│   │   └── tui.py           # Textual UI (consumes daemon)               │
│   ├── daemon/              # Background service                         │
│   │   ├── __init__.py                                                   │
│   │   ├── server.py        # gRPC server implementation                 │
│   │   ├── event_bus.py     # Internal pub/sub                           │
│   │   └── session.py       # Session state management                   │
│   ├── core/                # Shared business logic                      │
│   │   ├── plugins.py       # CommandRegistry (existing)                 │
│   │   └── base.py          # CommandResult (existing)                   │
│   └── memory/              # Memory systems                             │
│       └── __init__.py      # LocalMemoryBank (existing)                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Deliverables:**
- [ ] `jcapy-cli` client connects to local daemon
- [ ] ZeroMQ streaming for real-time logs
- [ ] TUI refactor to consume stream instead of local pipes
- [ ] Alpha release for internal dogfooding

### Phase 3: Context Engineering (Week 5-6)

**Goal:** Adopt Acontext terminology and implement metadata catalog.

```python
# src/jcapy/daemon/context.py - Context Engine

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

@dataclass
class Session:
    """First-class session concept (Acontext alignment)."""
    id: str
    created_at: datetime
    working_directory: str
    command_history: List[str] = field(default_factory=list)
    trajectory: List['TrajectoryEvent'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrajectoryEvent:
    """A single event in the session trajectory."""
    timestamp: datetime
    event_type: str  # 'command', 'observation', 'result', 'error'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextEngine:
    """
    The unified context management system.
    Aligns with Acontext's "Context Data Platform" concept.
    """
    def __init__(self, persistence_path: str = "~/.jcapy"):
        self.persistence_path = os.path.expanduser(persistence_path)
        self.sessions: Dict[str, Session] = {}
        self.current_session: Optional[Session] = None
        self._load_sessions()

    def create_session(self, working_directory: str) -> Session:
        """Create a new session."""
        import uuid
        session = Session(
            id=str(uuid.uuid4())[:8],
            created_at=datetime.now(),
            working_directory=working_directory
        )
        self.sessions[session.id] = session
        self.current_session = session
        self._persist_sessions()
        return session

    def record_event(self, event_type: str, content: str, metadata: Dict = None):
        """Record a trajectory event in the current session."""
        if not self.current_session:
            return
        
        event = TrajectoryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            content=content,
            metadata=metadata or {}
        )
        self.current_session.trajectory.append(event)
        self._persist_sessions()

    def _persist_sessions(self):
        """Save sessions to disk."""
        sessions_file = os.path.join(self.persistence_path, "sessions.json")
        os.makedirs(self.persistence_path, exist_ok=True)
        
        data = {
            "sessions": {
                sid: {
                    "id": s.id,
                    "created_at": s.created_at.isoformat(),
                    "working_directory": s.working_directory,
                    "command_history": s.command_history,
                    "trajectory": [
                        {
                            "timestamp": e.timestamp.isoformat(),
                            "event_type": e.event_type,
                            "content": e.content,
                            "metadata": e.metadata
                        }
                        for e in s.trajectory
                    ]
                }
                for sid, s in self.sessions.items()
            }
        }
        
        with open(sessions_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_sessions(self):
        """Load sessions from disk."""
        sessions_file = os.path.join(self.persistence_path, "sessions.json")
        if not os.path.exists(sessions_file):
            return
        
        try:
            with open(sessions_file, 'r') as f:
                data = json.load(f)
            
            for sid, sdata in data.get("sessions", {}).items():
                session = Session(
                    id=sdata["id"],
                    created_at=datetime.fromisoformat(sdata["created_at"]),
                    working_directory=sdata["working_directory"],
                    command_history=sdata.get("command_history", []),
                    trajectory=[
                        TrajectoryEvent(
                            timestamp=datetime.fromisoformat(e["timestamp"]),
                            event_type=e["event_type"],
                            content=e["content"],
                            metadata=e.get("metadata", {})
                        )
                        for e in sdata.get("trajectory", [])
                    ]
                )
                self.sessions[sid] = session
        except Exception:
            pass  # Corrupted file, start fresh
```

**Deliverables:**
- [ ] `ContextEngine` class with session management
- [ ] `index.json` metadata catalog for skills
- [ ] Session persistence (SQLite or JSON)
- [ ] Terminology alignment in all docstrings

### Phase 4: Integration (Week 7-8)

**Goal:** Build Acontext integration layer.

```python
# src/jcapy/services/acontext_provider.py - Acontext Backend Provider

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import httpx

class ContextProvider(ABC):
    """Abstract base class for context backends."""
    
    @abstractmethod
    async def store_trajectory(self, session_id: str, events: List[Dict]) -> bool:
        """Store session trajectory."""
        pass
    
    @abstractmethod
    async def recall(self, query: str, n_results: int = 5) -> List[Dict]:
        """Semantic search over context."""
        pass
    
    @abstractmethod
    async def sync_skills(self, skills: List[Dict]) -> bool:
        """Sync skill registry."""
        pass


class AcontextProvider(ContextProvider):
    """
    Integration with Acontext Context Data Platform.
    Enables JCapy to use Acontext as a cloud backend.
    """
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.acontext.io"):
        self.api_key = api_key or os.getenv("ACONTEXT_API_KEY")
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )
    
    async def store_trajectory(self, session_id: str, events: List[Dict]) -> bool:
        """Store session trajectory in Acontext."""
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/sessions/{session_id}/trajectory",
                json={"events": events}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def recall(self, query: str, n_results: int = 5) -> List[Dict]:
        """Semantic search via Acontext."""
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/recall",
                json={"query": query, "n_results": n_results}
            )
            if response.status_code == 200:
                return response.json().get("results", [])
            return []
        except Exception:
            return []
    
    async def sync_skills(self, skills: List[Dict]) -> bool:
        """Sync local skills to Acontext registry."""
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/skills/batch",
                json={"skills": skills}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        await self.client.aclose()


class HybridContextProvider(ContextProvider):
    """
    Hybrid provider: Local-first with cloud sync.
    Falls back to local ChromaDB when offline.
    """
    
    def __init__(self, local_provider, cloud_provider: Optional[AcontextProvider] = None):
        self.local = local_provider
        self.cloud = cloud_provider
    
    async def store_trajectory(self, session_id: str, events: List[Dict]) -> bool:
        # Always store locally first
        local_success = await self.local.store_trajectory(session_id, events)
        
        # Try cloud sync (non-blocking)
        if self.cloud:
            try:
                await self.cloud.store_trajectory(session_id, events)
            except Exception:
                pass  # Cloud unavailable, local is sufficient
        
        return local_success
    
    async def recall(self, query: str, n_results: int = 5) -> List[Dict]:
        # Try cloud first for freshest results
        if self.cloud:
            try:
                results = await self.cloud.recall(query, n_results)
                if results:
                    return results
            except Exception:
                pass
        
        # Fallback to local
        return await self.local.recall(query, n_results)
    
    async def sync_skills(self, skills: List[Dict]) -> bool:
        local_success = await self.local.sync_skills(skills)
        
        if self.cloud:
            try:
                await self.cloud.sync_skills(skills)
            except Exception:
                pass
        
        return local_success
```

**Deliverables:**
- [ ] `ContextProvider` abstract interface
- [ ] `AcontextProvider` implementation
- [ ] `HybridContextProvider` for local-first with cloud sync
- [ ] `jcapy-skill-acontext` plugin package
- [ ] Beta release with Acontext integration

---

## 6. Security Architecture

### 6.1 Zero-Trust IPC

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY: ZERO-TRUST IPC                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐                      ┌─────────────┐                 │
│   │ jcapy-cli   │                      │   jcapyd    │                 │
│   │             │                      │             │                 │
│   │ ┌─────────┐ │    mTLS Tunnel      │ ┌─────────┐ │                 │
│   │ │ Client  │ │ ════════════════════►│ │ Server  │ │                 │
│   │ │ Cert    │ │    Encrypted         │ │ Cert    │ │                 │
│   │ └─────────┘ │ ◄════════════════════│ └─────────┘ │                 │
│   │             │    Channel           │             │                 │
│   └─────────────┘                      └─────────────┘                 │
│                                                                         │
│   SOCKET PERMISSIONS:                                                   │
│   • Unix domain socket: mode 0600 (user-only)                          │
│   • TCP socket: localhost only (127.0.0.1)                             │
│   • Certificate pinning for all connections                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Plugin Sandboxing (WASM)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY: WASM SANDBOXING                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        jcapyd (Daemon)                          │  │
│   │                                                                 │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │                  Plugin Host                             │  │  │
│   │   │                                                         │  │  │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │  │
│   │   │   │  Plugin A   │  │  Plugin B   │  │  Plugin C   │    │  │  │
│   │   │   │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │    │  │  │
│   │   │   │ │  WASM   │ │  │ │  WASM   │ │  │ │  WASM   │ │    │  │  │
│   │   │   │ │ Runtime  │ │  │ │ Runtime  │ │  │ │ Runtime  │ │    │  │  │
│   │   │   │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │    │  │  │
│   │   │   │             │  │             │  │             │    │  │  │
│   │   │   │ Capabilities│  │ Capabilities│  │ Capabilities│    │  │  │
│   │   │   │ • fs:read   │  │ • network  │  │ • fs:write  │    │  │  │
│   │   │   │ • fs:write  │  │   :read    │  │   :/tmp     │    │  │  │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘    │  │  │
│   │   │                                                         │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   CAPABILITY MODEL:                                                     │
│   • Plugins must declare required capabilities in jcapy.yaml           │
│   • Runtime enforces capability boundaries                             │
│   • No direct filesystem/network access without permission             │
│   • Memory isolation between plugins                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 The Vault (Secret Management)

```python
# src/jcapy/daemon/vault.py - Secret Management

import keyring
from cryptography.fernet import Fernet
from typing import Optional
import os
import json

class Vault:
    """
    Encrypted secret storage using OS keyring.
    Never stores secrets in plaintext.
    """
    
    SERVICE_NAME = "jcapy"
    
    def __init__(self):
        self._cache: dict = {}
        self._fernet: Optional[Fernet] = None
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key from OS keyring."""
        key = keyring.get_password(self.SERVICE_NAME, "_vault_key")
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password(self.SERVICE_NAME, "_vault_key", key)
        return key.encode()
    
    def _get_fernet(self) -> Fernet:
        if not self._fernet:
            self._fernet = Fernet(self._get_or_create_key())
        return self._fernet
    
    def store(self, key: str, value: str) -> bool:
        """Store an encrypted secret."""
        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(value.encode())
            keyring.set_password(self.SERVICE_NAME, key, encrypted.decode())
            self._cache[key] = value
            return True
        except Exception:
            return False
    
    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve a decrypted secret."""
        if key in self._cache:
            return self._cache[key]
        
        try:
            encrypted = keyring.get_password(self.SERVICE_NAME, key)
            if not encrypted:
                return None
            
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(encrypted.encode()).decode()
            self._cache[key] = decrypted
            return decrypted
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a secret."""
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
            self._cache.pop(key, None)
            return True
        except Exception:
            return False
    
    def list_keys(self) -> list:
        """List all stored secret keys (not values)."""
        # This requires platform-specific implementation
        # For now, return cached keys
        return list(self._cache.keys())
```

---

## 7. Metrics & Observability

### 7.1 Telemetry Dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      JCAPY TELEMETRY DASHBOARD                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  SESSION METRICS                                                │  │
│   │  ─────────────────                                              │  │
│   │  • Total Sessions: 127                                          │  │
│   │  • Active Session: #a3f8b2c1                                    │  │
│   │  • Commands Executed: 1,847                                     │  │
│   │  • Success Rate: 94.2%                                          │  │
│   │  • Avg Response Time: 127ms                                     │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  AI USAGE                                                       │  │
│   │  ─────────                                                      │  │
│   │  • Tokens Used: 847,293                                         │  │
│   │  • Estimated Cost: $12.47                                       │  │
│   │  • Model: claude-3-sonnet                                       │  │
│   │  • Requests Today: 89                                           │  │
│   │                                                                 │  │
│   │  Cost Trend (7 days):                                           │  │
│   │  ▁▂▃▅▆▇█▆▅▃▂▁                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  MEMORY STATS                                                   │  │
│   │  ────────────                                                   │  │
│   │  • Skills Indexed: 47                                           │  │
│   │  • Vector DB Size: 12.3 MB                                      │  │
│   │  • Last Sync: 2 hours ago                                       │  │
│   │  • Recall Accuracy: 89.3%                                       │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Success Criteria

### 8.1 Phase Completion Checklist

| Phase | Criteria | Status |
|-------|----------|--------|
| **Phase 1** | gRPC daemon responds to ping | ⬜ |
| | Command execution via gRPC works | ⬜ |
| | Unit tests pass | ⬜ |
| **Phase 2** | TUI connects to daemon | ⬜ |
| | Real-time log streaming works | ⬜ |
| | Session persists after TUI close | ⬜ |
| **Phase 3** | Sessions stored in SQLite/JSON | ⬜ |
| | Terminology aligned with Acontext | ⬜ |
| | index.json catalog generated | ⬜ |
| **Phase 4** | AcontextProvider connects to API | ⬜ |
| | Hybrid fallback works offline | ⬜ |
| | Skills sync to cloud | ⬜ |

### 8.2 Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| TUI startup time | < 100ms | Time from `jcapy` to interactive |
| Command latency | < 50ms | Round-trip to daemon |
| Memory recall | < 200ms | Semantic search response |
| Offline capability | 100% | All core features work offline |
| Cloud sync latency | < 2s | Full skill sync to Acontext |

---

## 9. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| gRPC complexity | Medium | High | Start with simple proto, iterate |
| Breaking existing TUI | Medium | High | Feature flag for daemon mode |
| Acontext API changes | Low | Medium | Abstract provider interface |
| Performance regression | Medium | High | Benchmark suite in CI |
| Security vulnerabilities | Low | Critical | Security audit before release |

---

## 10. Conclusion

The **Orbital Architecture** positions JCapy as the definitive **local-first context platform** for the one-army developer. By adopting Acontext-inspired patterns (Sessions, Trajectory, Context Engine) while maintaining its unique advantages (privacy, offline-first, terminal-native), JCapy can:

1. **Own the local niche** - No competitor offers this level of local-first context management
2. **Integrate with enterprise** - Acontext integration enables team observability when needed
3. **Scale indefinitely** - Daemon architecture supports future web/mobile clients
4. **Stay secure** - Zero-trust IPC and WASM sandboxing protect the "keys to the kingdom"

**Next Step:** Begin Phase 1 implementation with `jcapy.proto` and daemon skeleton.

---

*Document Version: 1.0*
*Last Updated: 2026-02-19*
*Author: JCapy Architecture Team*
