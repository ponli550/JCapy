#!/bin/bash
set -e

# Role: SRE ("The Firefighter")
# Goal: Rapid system diagnostics during an outage.

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

function step() {
    sleep 1
    echo -e "\n${CYAN}STEP $1: $2${RESET}"
    echo -e "${YELLOW}------------------------------------------${RESET}"
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JCAPY_BIN="$PROJECT_ROOT/.venv/bin/jcapy"

echo -e "${CYAN}🚀 Scenario: The Firefighter${RESET}"
echo -e "SRE: 'Uptime is a mindset, not a metric.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Incident Workspace"
"$JCAPY_BIN" init --grade A

step 2 "Drafting Diagnostic Script"
cat <<EOF > check_health.sh
#!/bin/bash
echo "🚑 System Health Check"
echo "----------------------"
echo "Load Average:"
uptime
echo ""
echo "Memory Usage:"
free -h
echo ""
echo "Disk Space:"
df -h | grep '/$'
echo ""
echo "Active Connections:"
netstat -an | grep ESTABLISHED | wc -l
echo "----------------------"
echo "✅ Diagnostics Complete."
EOF
chmod +x check_health.sh
echo -e "${GREEN}✔ Created check_health.sh${RESET}"

step 3 "Harvesting Diagnostic Tool"
"$JCAPY_BIN" harvest \
    --doc check_health.sh \
    --name "System Health Check" \
    --desc "Rapid diagnostics for incident response" \
    --grade A \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Running Diagnostics on Production"
"$JCAPY_BIN" apply "system_health_check" --dry-run
