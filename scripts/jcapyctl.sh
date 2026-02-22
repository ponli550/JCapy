#!/bin/bash
# JCapy Control Script - Unified Entry Point
# Usage: ./jcapyctl.sh [command] [options]
#
# Commands:
#   daemon start|stop|restart|status  - Manage daemon
#   tunnel setup|start|stop|status    - Cloudflare tunnel
#   docker up|down|logs               - Docker management
#   health                            - Health check
#   open                              - Open control plane in browser

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Detect Python
JCAPY_PYTHON="/Users/irfanali/.local/pipx/venvs/jcapy/bin/python"
if [ ! -f "$JCAPY_PYTHON" ]; then
    JCAPY_PYTHON="python3"
fi

export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Banner
banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           JCAPY CONTROL CENTER                            ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Daemon commands
daemon_cmd() {
    case "${1:-}" in
        start)
            echo -e "${CYAN}Starting daemon...${NC}"
            $JCAPY_PYTHON -m jcapy.daemon.server --port 8080 &
            sleep 2
            echo -e "${GREEN}✓ Daemon started at http://localhost:8080${NC}"
            ;;
        stop)
            echo -e "${CYAN}Stopping daemon...${NC}"
            pkill -f "jcapy.daemon.server" 2>/dev/null || true
            echo -e "${GREEN}✓ Daemon stopped${NC}"
            ;;
        restart)
            daemon_cmd stop
            sleep 1
            daemon_cmd start
            ;;
        status)
            if pgrep -f "jcapy.daemon.server" > /dev/null; then
                echo -e "${GREEN}● Daemon running${NC}"
                curl -s http://localhost:8080/api/status | $JCAPY_PYTHON -m json.tool 2>/dev/null || echo "API not responding"
            else
                echo -e "${RED}○ Daemon stopped${NC}"
            fi
            ;;
        *)
            echo "Usage: $0 daemon {start|stop|restart|status}"
            ;;
    esac
}

# Tunnel commands
tunnel_cmd() {
    case "${1:-}" in
        setup|start|stop|status|logs)
            "$SCRIPT_DIR/cloudflare-tunnel.sh" "$@"
            ;;
        *)
            echo "Usage: $0 tunnel {setup|start|stop|status|logs}"
            ;;
    esac
}

# Docker commands
docker_cmd() {
    cd "$PROJECT_ROOT"
    case "${1:-}" in
        up)
            echo -e "${CYAN}Starting Docker containers...${NC}"
            docker-compose up -d
            echo -e "${GREEN}✓ Containers started${NC}"
            ;;
        down)
            echo -e "${CYAN}Stopping Docker containers...${NC}"
            docker-compose down
            echo -e "${GREEN}✓ Containers stopped${NC}"
            ;;
        logs)
            docker-compose logs -f jcapy
            ;;
        *)
            echo "Usage: $0 docker {up|down|logs}"
            ;;
    esac
}

# Health check
health_cmd() {
    echo -e "${CYAN}Checking JCapy health...${NC}"
    curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || \
        echo -e "${RED}✗ Daemon not responding${NC}"
}

# Open control plane
open_cmd() {
    echo -e "${CYAN}Opening Control Plane...${NC}"
    open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || \
        echo "Visit http://localhost:8080 in your browser"
}

# Main
case "${1:-}" in
    daemon)
        daemon_cmd "${2:-}"
        ;;
    tunnel)
        tunnel_cmd "${2:-}"
        ;;
    docker)
        docker_cmd "${2:-}"
        ;;
    health)
        health_cmd
        ;;
    open)
        open_cmd
        ;;
    *)
        banner
        echo "Usage: $0 {daemon|tunnel|docker|health|open} [options]"
        echo ""
        echo "Commands:"
        echo "  daemon start|stop|restart|status  Manage background daemon"
        echo "  tunnel setup|start|stop|status    Cloudflare tunnel"
        echo "  docker up|down|logs               Docker management"
        echo "  health                            Health check"
        echo "  open                              Open control plane in browser"
        ;;
esac
