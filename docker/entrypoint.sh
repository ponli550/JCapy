#!/bin/bash
# JCapy Docker Entrypoint Script
# Supports multiple run modes: daemon, web, cli, tui

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           JCAPY - One-Army Orchestrator                   ║"
echo "║                   v4.1.8 Daemon                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Default mode
MODE="${1:-daemon}"

# Environment setup
export JCAPY_HOME="${JCAPY_HOME:-/home/jcapy/.jcapy}"
export JCAPY_LOG_DIR="${JCAPY_LOG_DIR:-/app/logs}"
export JCAPY_DATA_DIR="${JCAPY_DATA_DIR:-/home/jcapy/.jcapy/data}"

# Ensure directories exist
mkdir -p "$JCAPY_HOME/skills" "$JCAPY_LOG_DIR" "$JCAPY_DATA_DIR"

# Function: Start daemon mode (background service + web)
start_daemon() {
    echo -e "${GREEN}[DAEMON] Starting JCapy background service...${NC}"
    
    # Start the web control plane
    echo -e "${CYAN}[WEB] Control Plane starting on port 8080...${NC}"
    
    # Create a simple health endpoint
    python3 -c "
import http.server
import socketserver
import json
import os

PORT = 8080
JCAPY_HOME = os.environ.get('JCAPY_HOME', '/home/jcapy/.jcapy')

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'service': 'jcapyd', 'version': '4.1.8'}
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''
<!DOCTYPE html>
<html>
<head>
    <title>JCapy Control Plane</title>
    <style>
        body { font-family: monospace; background: #0f172a; color: #e2e8f0; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #22d3ee; }
        .status { background: #1e293b; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .ok { color: #22c55e; }
        code { background: #334155; padding: 2px 8px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>🚀 JCapy Control Plane</h1>
        <div class=\"status\">
            <p><strong>Status:</strong> <span class=\"ok\">● Running</span></p>
            <p><strong>Version:</strong> 4.1.8</p>
            <p><strong>Mode:</strong> Daemon</p>
        </div>
        <h2>Quick Commands</h2>
        <pre>
docker exec -it jcapy-daemon jcapy --help
docker exec -it jcapy-daemon jcapy doctor
docker exec -it jcapy-daemon jcapy manage
        </pre>
        <h2>API Endpoints</h2>
        <ul>
            <li><code>GET /health</code> - Health check</li>
        </ul>
    </div>
</body>
</html>
'''
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', PORT), HealthHandler) as httpd:
    print(f'🚀 JCapy Control Plane active at http://localhost:{PORT}')
    httpd.serve_forever()
" &

    WEB_PID=$!
    echo "$WEB_PID" > "$JCAPY_LOG_DIR/web.pid"
    
    # Keep container running
    echo -e "${GREEN}[DAEMON] JCapy is running. Press Ctrl+C to stop.${NC}"
    echo -e "${CYAN}[INFO] Web Control Plane: http://localhost:8080${NC}"
    echo -e "${CYAN}[INFO] Health Check: http://localhost:8080/health${NC}"
    
    # Wait for web process
    wait $WEB_PID
}

# Function: Start web-only mode
start_web() {
    echo -e "${GREEN}[WEB] Starting Web Control Plane only...${NC}"
    cd /app
    python3 -m jcapy --web --port 8080
}

# Function: Start CLI mode
start_cli() {
    echo -e "${GREEN}[CLI] Starting JCapy CLI...${NC}"
    shift
    exec jcapy "$@"
}

# Function: Start TUI mode
start_tui() {
    echo -e "${GREEN}[TUI] Starting JCapy TUI Dashboard...${NC}"
    exec jcapy manage
}

# Function: Run doctor
run_doctor() {
    echo -e "${YELLOW}[DOCTOR] Running system diagnostics...${NC}"
    exec jcapy doctor
}

# Main switch
case "$MODE" in
    daemon)
        start_daemon
        ;;
    web)
        start_web
        ;;
    cli)
        start_cli "$@"
        ;;
    tui|manage)
        start_tui
        ;;
    doctor)
        run_doctor
        ;;
    help|--help|-h)
        echo "Usage: entrypoint.sh [MODE] [ARGS...]"
        echo ""
        echo "Modes:"
        echo "  daemon   - Background service with web control plane (default)"
        echo "  web      - Web control plane only"
        echo "  cli      - CLI mode (pass commands as additional args)"
        echo "  tui      - TUI dashboard mode"
        echo "  doctor   - Run system diagnostics"
        echo ""
        echo "Examples:"
        echo "  docker run jcapy daemon"
        echo "  docker run jcapy cli --help"
        echo "  docker run jcapy doctor"
        ;;
    *)
        echo -e "${YELLOW}Unknown mode: $MODE${NC}"
        echo "Running as CLI command..."
        exec jcapy "$@"
        ;;
esac