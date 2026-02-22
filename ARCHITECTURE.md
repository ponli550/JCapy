# JCapy Architecture

**Version**: 4.1.8  
**Last Updated**: February 2026

---

## Directory Structure

```
jcapy/
├── src/jcapy/              # Main source code
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── main.py             # CLI main function
│   ├── config.py           # Configuration management
│   ├── daemon/             # Background daemon module
│   │   ├── __init__.py
│   │   ├── server.py       # HTTP server + Control Plane
│   │   └── health.py       # Health monitoring
│   ├── commands/           # CLI commands
│   │   ├── daemon_cmd.py   # Daemon management
│   │   ├── brain.py        # Knowledge management
│   │   ├── doctor.py       # Diagnostics
│   │   └── ...
│   ├── core/               # Core framework
│   │   ├── plugins.py      # Plugin registry
│   │   ├── bootstrap.py    # Command registration
│   │   └── ...
│   ├── ui/                 # Textual TUI
│   ├── mcp/                # MCP server
│   ├── memory/             # Memory/ChromaDB
│   └── utils/              # Utilities
│
├── apps/                   # Web applications
│   └── web/                # React/Vite web app
│
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── services/               # System service files
│   ├── com.jcapy.daemon.plist  # macOS launchd
│   └── jcapy-daemon.service    # Linux systemd
│
├── scripts/                # Utility scripts
│   ├── jcapyctl.sh         # Unified control script
│   ├── cloudflare-tunnel.sh
│   ├── setup.sh
│   └── publish.sh
│
├── docs/                   # Documentation
│   ├── DAEMON_DEPLOYMENT.md
│   ├── guides/
│   └── plans/
│
├── tests/                  # Test suite
├── examples/               # Example plugins
├── jcapy-skills/           # Curated skills
├── showcase/               # Demo use cases
│
├── docker-compose.yml      # Docker Compose config
├── pyproject.toml          # Python package config
└── README.md
```

---

## Components

### 1. CLI (`jcapy`)

The main command-line interface:

```bash
jcapy                  # Launch TUI dashboard
jcapy --help           # Show help
jcapy daemon start     # Start background daemon
jcapy doctor           # Run diagnostics
```

### 2. TUI Dashboard

Interactive Textual-based dashboard:

```bash
jcapy           # Launch dashboard
jcapy manage    # Same as above
```

### 3. Daemon Server

Background HTTP server with Control Plane:

```bash
jcapy daemon start    # Start on port 8080
jcapy daemon status   # Check status
jcapy daemon stop     # Stop daemon
```

**Endpoints:**
- `/` - Control Plane UI
- `/health` - Health check
- `/api/status` - Status JSON
- `/api/metrics` - Prometheus metrics

### 4. Docker

Containerized deployment:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### 5. Cloudflare Tunnel

Secure remote access:

```bash
./scripts/cloudflare-tunnel.sh setup
./scripts/cloudflare-tunnel.sh start
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Launch TUI | `jcapy` |
| Start daemon | `jcapy daemon start` |
| Check health | `curl localhost:8080/health` |
| Docker up | `docker-compose up -d` |
| Control script | `./scripts/jcapyctl.sh` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        JCAPY                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    CLI      │  │    TUI      │  │   Daemon    │        │
│  │  (jcapy)    │  │ (Textual)   │  │  (HTTP:8080)│        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│  ┌───────────────────────▼───────────────────────────┐    │
│  │              Core Framework                        │    │
│  │  • Plugin Registry  • Command System  • Config    │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │              Services                              │    │
│  │  • Memory (ChromaDB)  • MCP Server  • Skills      │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘