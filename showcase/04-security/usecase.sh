#!/bin/bash
set -e

# Role: Security Engineer ("The Paranoiac")
# Goal: Automate security audits on every commit.

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

echo -e "${CYAN}🚀 Scenario: The Paranoiac${RESET}"
echo -e "SecEng: 'Trust nothing. Audit everything.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Secure Project"
"$JCAPY_BIN" init --grade A

step 2 "Drafting Security Audit Script"
cat <<EOF > audit_security.sh
#!/bin/bash
# SECURITY AUDIT v1.0
echo "🔒 Starting Security Scan..."

echo "1. Checking for Secrets..."
grep -r "API_KEY" . || echo "   ✔ No exposed secrets found."

echo "2. Scanning Dependencies..."
# Simulating pip audit
echo "   ✔ Python dependencies secure."
# Simulating npm audit
echo "   ✔ Node dependencies secure."

echo "3. File Permissions..."
find . -type f -perm 777 && echo "   ⚠️  Insecure permissions found!" || echo "   ✔ Permissions tight."

echo "✅ Audit Complete."
EOF
chmod +x audit_security.sh
echo -e "${GREEN}✔ Created audit_security.sh${RESET}"

step 3 "Harvesting Security Protocol"
"$JCAPY_BIN" harvest \
    --doc audit_security.sh \
    --name "Security Audit Protocol" \
    --desc "Basic secret and dependency scanner" \
    --grade A \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Running Audit on CI/CD Target"
"$JCAPY_BIN" apply "security_audit_protocol" --dry-run
