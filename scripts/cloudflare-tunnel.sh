#!/bin/bash
# JCapy Cloudflare Tunnel Setup Script
# Creates a secure tunnel to expose the JCapy Control Plane to the internet
#
# Usage:
#   ./cloudflare-tunnel.sh setup    - Create and configure tunnel
#   ./cloudflare-tunnel.sh start    - Start the tunnel
#   ./cloudflare-tunnel.sh stop     - Stop the tunnel
#   ./cloudflare-tunnel.sh status   - Check tunnel status
#   ./cloudflare-tunnel.sh logs     - View tunnel logs
#
# Prerequisites:
#   1. Cloudflare account
#   2. Domain managed by Cloudflare
#   3. cloudflared installed (brew install cloudflare/cloudflare/cloudflared)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
TUNNEL_NAME="jcapy-daemon"
CONFIG_DIR="$HOME/.jcapy/tunnel"
CONFIG_FILE="$CONFIG_DIR/config.yml"
CREDENTIALS_FILE="$CONFIG_DIR/credentials.json"
LOCAL_PORT=8080

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        JCAPY CLOUDFLARE TUNNEL SETUP                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if cloudflared is installed
check_cloudflared() {
    if ! command -v cloudflared &> /dev/null; then
        echo -e "${RED}Error: cloudflared is not installed${NC}"
        echo ""
        echo "Install with:"
        echo "  macOS:   brew install cloudflare/cloudflare/cloudflared"
        echo "  Linux:   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared"
        echo "           sudo mv cloudflared /usr/local/bin/"
        echo "           sudo chmod +x /usr/local/bin/cloudflared"
        exit 1
    fi
    echo -e "${GREEN}✓ cloudflared is installed${NC}"
}

# Check if user is logged in
check_login() {
    if ! cloudflared tunnel list &> /dev/null; then
        echo -e "${YELLOW}Not logged in to Cloudflare${NC}"
        echo "Opening browser for authentication..."
        cloudflared tunnel login
    fi
    echo -e "${GREEN}✓ Authenticated with Cloudflare${NC}"
}

# Setup tunnel
setup_tunnel() {
    echo -e "${CYAN}Setting up Cloudflare Tunnel...${NC}"
    
    check_cloudflared
    check_login
    
    # Create config directory
    mkdir -p "$CONFIG_DIR"
    
    # Check if tunnel already exists
    if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
        echo -e "${YELLOW}Tunnel '$TUNNEL_NAME' already exists${NC}"
    else
        echo "Creating tunnel '$TUNNEL_NAME'..."
        cloudflared tunnel create "$TUNNEL_NAME"
        echo -e "${GREEN}✓ Tunnel created${NC}"
    fi
    
    # Get tunnel ID
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo -e "${CYAN}Tunnel ID: $TUNNEL_ID${NC}"
    
    # Ask for domain
    echo ""
    echo -e "${YELLOW}Enter your Cloudflare domain (e.g., example.com):${NC}"
    read -r DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}Domain is required${NC}"
        exit 1
    fi
    
    # Create config file
    echo "Creating configuration file..."
    cat > "$CONFIG_FILE" << EOF
# JCapy Cloudflare Tunnel Configuration
# Generated: $(date)

tunnel: $TUNNEL_ID
credentials-file: $CREDENTIALS_FILE

ingress:
  # Route jcapy subdomain to local daemon
  - hostname: jcapy.$DOMAIN
    service: http://localhost:$LOCAL_PORT
    
  # Health check endpoint
  - hostname: jcapy.$DOMAIN
    path: /health
    service: http://localhost:$LOCAL_PORT/health
    
  # Catch-all rule (required)
  - service: http_status:404

# Logging
logfile: $CONFIG_DIR/tunnel.log
loglevel: info
EOF
    
    echo -e "${GREEN}✓ Configuration created at $CONFIG_FILE${NC}"
    
    # Copy credentials
    CRED_SOURCE="$HOME/.cloudflared/$TUNNEL_ID.json"
    if [ -f "$CRED_SOURCE" ]; then
        cp "$CRED_SOURCE" "$CREDENTIALS_FILE"
        echo -e "${GREEN}✓ Credentials copied${NC}"
    fi
    
    # Create DNS record
    echo ""
    echo -e "${YELLOW}Create DNS record for jcapy.$DOMAIN? (y/n)${NC}"
    read -r CREATE_DNS
    
    if [ "$CREATE_DNS" = "y" ]; then
        cloudflared tunnel route dns "$TUNNEL_NAME" "jcapy.$DOMAIN"
        echo -e "${GREEN}✓ DNS record created${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}Tunnel setup complete!${NC}"
    echo ""
    echo -e "Your JCapy Control Plane will be available at:"
    echo -e "${CYAN}https://jcapy.$DOMAIN${NC}"
    echo ""
    echo "Start the tunnel with:"
    echo -e "${CYAN}  ./cloudflare-tunnel.sh start${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
}

# Start tunnel
start_tunnel() {
    echo -e "${CYAN}Starting Cloudflare Tunnel...${NC}"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}Tunnel not configured. Run './cloudflare-tunnel.sh setup' first${NC}"
        exit 1
    fi
    
    # Check if already running
    if pgrep -f "cloudflared tunnel run" > /dev/null; then
        echo -e "${YELLOW}Tunnel is already running${NC}"
        return
    fi
    
    # Start in background
    nohup cloudflared tunnel --config "$CONFIG_FILE" run > "$CONFIG_DIR/tunnel.log" 2>&1 &
    
    sleep 2
    
    if pgrep -f "cloudflared tunnel run" > /dev/null; then
        echo -e "${GREEN}✓ Tunnel started${NC}"
        echo ""
        echo "View logs: ./cloudflare-tunnel.sh logs"
        echo "Stop tunnel: ./cloudflare-tunnel.sh stop"
    else
        echo -e "${RED}Failed to start tunnel. Check logs at $CONFIG_DIR/tunnel.log${NC}"
    fi
}

# Stop tunnel
stop_tunnel() {
    echo -e "${CYAN}Stopping Cloudflare Tunnel...${NC}"
    
    if pgrep -f "cloudflared tunnel run" > /dev/null; then
        pkill -f "cloudflared tunnel run"
        echo -e "${GREEN}✓ Tunnel stopped${NC}"
    else
        echo -e "${YELLOW}Tunnel is not running${NC}"
    fi
}

# Check status
status_tunnel() {
    echo -e "${CYAN}Cloudflare Tunnel Status${NC}"
    echo "─────────────────────────────────"
    
    if pgrep -f "cloudflared tunnel run" > /dev/null; then
        PID=$(pgrep -f "cloudflared tunnel run")
        echo -e "Status: ${GREEN}● Running${NC}"
        echo "PID: $PID"
        
        if [ -f "$CONFIG_FILE" ]; then
            # Extract domain from config
            DOMAIN=$(grep "hostname:" "$CONFIG_FILE" | head -1 | awk '{print $2}')
            echo "URL: https://$DOMAIN"
        fi
    else
        echo -e "Status: ${RED}○ Stopped${NC}"
    fi
    
    echo ""
    
    # Check local daemon
    echo -e "${CYAN}Local Daemon Status${NC}"
    echo "─────────────────────────────────"
    
    if curl -s "http://localhost:$LOCAL_PORT/health" > /dev/null 2>&1; then
        echo -e "Status: ${GREEN}● Running${NC}"
        echo "URL: http://localhost:$LOCAL_PORT"
    else
        echo -e "Status: ${RED}○ Not responding${NC}"
        echo "Start with: jcapy daemon start"
    fi
}

# View logs
logs_tunnel() {
    LOG_FILE="$CONFIG_DIR/tunnel.log"
    
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}No log file found${NC}"
        return
    fi
    
    echo -e "${CYAN}Tunnel Logs (last 50 lines):${NC}"
    echo "─────────────────────────────────"
    tail -n 50 "$LOG_FILE"
}

# Main
case "${1:-}" in
    setup)
        setup_tunnel
        ;;
    start)
        start_tunnel
        ;;
    stop)
        stop_tunnel
        ;;
    restart)
        stop_tunnel
        sleep 1
        start_tunnel
        ;;
    status)
        status_tunnel
        ;;
    logs)
        logs_tunnel
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  setup   - Create and configure tunnel"
        echo "  start   - Start the tunnel"
        echo "  stop    - Stop the tunnel"
        echo "  restart - Restart the tunnel"
        echo "  status  - Check tunnel status"
        echo "  logs    - View tunnel logs"
        exit 1
        ;;
esac