# JCapy Daemon Production Deployment Guide

**Version**: 2.0.0-alpha.1 (Orbital Foundation)
**Last Updated**: February 2026

---

## Overview

JCapy can run as a background daemon with a web-based Control Plane for monitoring and management. This guide covers multiple deployment options:

| Method | Best For | Complexity |
|--------|----------|------------|
| **Direct Daemon** | Local development | ⭐ |
| **System Service** | Always-on background | ⭐⭐ |
| **Docker** | Containerized deployment | ⭐⭐ |
| **Cloudflare Tunnel** | Secure remote access | ⭐⭐⭐ |

---

## Quick Start

### Option 1: Direct Daemon (Recommended for Development)

```bash
# Start daemon
jcapy daemon start

# Check status
jcapy daemon status

# View logs
jcapy daemon logs

# Stop daemon
jcapy daemon stop
```

Access the Control Plane at: **http://localhost:8080**

### Option 2: Docker (Recommended for Production)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f jcapy

# Stop
docker-compose down
```

---

## Detailed Deployment

### 1. Direct Daemon Mode

The simplest way to run JCapy as a background service.

```bash
# Start on custom port
jcapy daemon start --port 9000

# Check if running
jcapy daemon status

# Run health check
jcapy daemon health

# View logs (last 100 lines)
jcapy daemon logs --lines 100
```

**Endpoints:**
- Control Plane (UI): `http://localhost:8080/`
- Health Check (JSON): `http://localhost:8080/health`
- JCapy Brain (gRPC): `localhost:50051`
- Event Bus (ZMQ PUB): `localhost:5555`
- Command RPC (ZMQ RPC): `localhost:5556`
- Status API: `http://localhost:8080/api/status`
- Metrics: `http://localhost:8080/api/metrics`

### 2. System Service (macOS - launchd)

Install JCapy as a macOS launch agent for automatic startup.

```bash
# Install service
./scripts/daemon.sh install

# Start service
launchctl load ~/Library/LaunchAgents/com.jcapy.daemon.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.jcapy.daemon.plist

# Check status
launchctl list | grep jcapy

# Uninstall
100: ./scripts/daemon.sh uninstall
```

**Log locations:**
- Standard output: `~/.jcapy/logs/daemon.log`
- Errors: `~/.jcapy/logs/daemon.error.log`

### 3. System Service (Linux - systemd)

Install JCapy as a systemd service.

```bash
# Install service
./scripts/daemon.sh install

# Start service
sudo systemctl start jcapy-daemon

# Enable auto-start on boot
sudo systemctl enable jcapy-daemon

# Check status
sudo systemctl status jcapy-daemon

# View logs
journalctl -u jcapy-daemon -f

# Stop service
sudo systemctl stop jcapy-daemon

# Uninstall
./scripts/daemon.sh uninstall
```

### 4. Docker Deployment

Run JCapy in a containerized environment.

```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f jcapy

# Execute commands inside container
docker exec -it jcapy-daemon jcapy --help
docker exec -it jcapy-daemon jcapy doctor

# Restart
docker-compose restart jcapy

# Stop and remove
docker-compose down
```

**With Cloudflare Tunnel:**

```bash
# Set your tunnel token
export CLOUDFLARE_TUNNEL_TOKEN=your_token_here

# Start with tunnel
docker-compose --profile tunnel up -d
```

**With Redis cache:**

```bash
docker-compose --profile cache up -d
```

### 5. Cloudflare Tunnel (Remote Access)

Expose your local JCapy daemon securely to the internet.

**Prerequisites:**
1. Cloudflare account
2. Domain managed by Cloudflare
3. `cloudflared` installed

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Setup tunnel (interactive)
./scripts/cloudflare-tunnel.sh setup

# Start tunnel
./scripts/cloudflare-tunnel.sh start

# Check status
./scripts/cloudflare-tunnel.sh status

# View logs
./scripts/cloudflare-tunnel.sh logs

# Stop tunnel
./scripts/cloudflare-tunnel.sh stop
```

Your JCapy Control Plane will be available at: **https://jcapy.yourdomain.com**

---

## Architecture (v2.0 Orbital)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER (CLIENTS)                    │
│  ┌──────────────────────┐           ┌──────────────────────┐             │
│  │      main.py         │           │      ui/app.py       │             │
│  │   (Stateless CLI)    │           │    (Stateless TUI)   │             │
│  └──────────┬───────────┘           └───────────┬──────────┘             │
└─────────────┼───────────────────────────────────┼────────────────────────┘
              │             RPC / ZMQ             │
              ▼            Local Bridge           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         JCAPY BRAIN (DAEMON)                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                daemon/server.py (jcapyd Service)                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │  │
│  │  │ gRPC Server │  │ ZMQ Publisher │  │   Control Plane (HTTP)   │  │  │
│  │  │   :50051    │  │   :5555     │  │      :8080           │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────┬────────────────────────────────┘  │
│                                     │                                    │
│  ┌──────────────────────────────────▼────────────────────────────────┐  │
│  │                   core/service.py (Service Layer)                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │  │
│  │  │ Command Hub │  │ Bus Broadcas │  │    Log Virtualizer       │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────────────┼────────────────────────────────────┘
```

---

## API Reference

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "jcapyd",
  "version": "2.0.0-alpha.1",
  "timestamp": "2026-02-21T00:00:00.000000"
}
```

### Status

```bash
GET /api/status
```

Response:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "uptime_human": "1h 0m 0s",
  "active_sessions": 0,
  "tasks_completed": 42,
  "last_activity": "2026-02-21T00:00:00.000000",
  "version": "2.0.0-alpha.1"
}
```

### Metrics (Prometheus format)

```bash
GET /api/metrics
```

Response:
```
# HELP jcapy_uptime_seconds Daemon uptime in seconds
# TYPE jcapy_uptime_seconds counter
jcapy_uptime_seconds 3600

# HELP jcapy_tasks_completed Total tasks completed
# TYPE jcapy_tasks_completed counter
jcapy_tasks_completed 42

# HELP jcapy_active_sessions Active sessions
# TYPE jcapy_active_sessions gauge
jcapy_active_sessions 0
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JCAPY_HOME` | `~/.jcapy` | JCapy home directory |
| `JCAPY_LOG_DIR` | `~/.jcapy/logs` | Log directory |
| `JCAPY_DAEMON_MODE` | `0` | Set to `1` for daemon mode |
| `JCAPY_PID_FILE` | `~/.jcapy/daemon.pid` | PID file location |
| `JCAPY_PORT` | `8080` | Default port |

### Directory Structure

```
~/.jcapy/
├── config.yaml       # Configuration file
├── daemon.pid        # PID file (when running)
├── skills/           # Installed plugins
├── data/             # Data storage
├── logs/
│   ├── daemon.log        # Standard output
│   └── daemon.error.log  # Error output
└── tunnel/
    ├── config.yml        # Cloudflare tunnel config
    ├── credentials.json  # Tunnel credentials
    └── tunnel.log        # Tunnel logs
```

---

## Troubleshooting

### Daemon won't start

```bash
# Check if port is in use
lsof -i :8080

# Check logs
jcapy daemon logs

# Run health check
jcapy daemon health

# Try different port
jcapy daemon start --port 9000
```

### Permission issues

```bash
# Fix permissions
chmod -R 755 ~/.jcapy
```

### Docker issues

```bash
# Rebuild container
docker-compose build --no-cache

# Check container logs
docker-compose logs jcapy

# Check container health
docker inspect jcapy-daemon | grep -A 10 Health
```

### Cloudflare tunnel issues

```bash
# Check cloudflared version
cloudflared --version

# Re-authenticate
cloudflared tunnel login

# Check tunnel status
cloudflared tunnel list

# View tunnel logs
./scripts/cloudflare-tunnel.sh logs
```

---

## Security Considerations

1. **Local Access Only**: By default, the daemon binds to `localhost`. For external access, use Cloudflare Tunnel.

2. **No Authentication**: The Control Plane has no built-in authentication. Use Cloudflare Access or a reverse proxy for production.

3. **HTTPS**: Cloudflare Tunnel provides automatic HTTPS. For direct access, use a reverse proxy.

4. **Firewall**: If binding to `0.0.0.0`, ensure firewall rules restrict access.

---

## Support

- **Documentation**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/ponli550/JCapy/issues)
- **Community**: One-Army Movement ❤️
