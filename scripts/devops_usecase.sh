#!/bin/bash
set -e

# DevOps User Journey: "Ideally LazyOps"
# Goal: Build infrastructure once, reuse forever.

# Function for visual hierarchy
function step() {
    sleep 1 # Pause for dramatic effect/readability
    echo -e "\n${CYAN}STEP $1: $2${RESET}"
    echo -e "${YELLOW}------------------------------------------${RESET}"
}

# ANSI Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}🚀 Starting DevOps User Journey: 'Ideally LazyOps'${RESET}"

# Determine local jcapy path
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JCAPY_BIN="$PROJECT_ROOT/.venv/bin/jcapy"

echo -e "${YELLOW}🔧 Using JCapy at: ${JCAPY_BIN}${RESET}"

# Create a temporary environment to simulate a new project
DEMO_DIR=$(mktemp -d)
echo -e "${YELLOW}📂 Created clean workspace: ${DEMO_DIR}${RESET}"

# Ensure we cleanup on exit
trap "rm -rf $DEMO_DIR" EXIT

cd "$DEMO_DIR"

# 1. New Project Initialization (Grade A: Fortress)
# DevOps Dave is starting a serious infrastructure project.
step 1 "Initializing 'Fortress' Infrastructure Project"
"$JCAPY_BIN" init --grade A

# Verify structure
if [ -d "docker" ] && [ -f ".jcapyrc" ]; then
    echo -e "${GREEN}✔ Fortress-grade structure verified.${RESET}"
else
    echo -e "${RED}❌ Project initialization failed.${RESET}"
    exit 1
fi

# 2. Simulating Infrastructure Code Creation
step 2 "Writing 'Golden' Provisioning Script"
cat <<EOF > provision_k8s.sh
#!/bin/bash
# PROVISIONING SCRIPT (v1.0)
echo "📦 Installing Dependencies..."
echo "  - Docker Engine"
echo "  - Kubectl"
echo "  - Helm"
echo "🔒 Applying Security Hardening..."
echo "  - UFW Enable"
echo "  - SSH Key Only"
echo "🚀 Deploying Cluster..."
echo "  - K3s Init"
echo "✅ Cluster Provisioned Successfully."
EOF
chmod +x provision_k8s.sh

echo -e "${GREEN}✔ Created provision_k8s.sh (The Golden Template)${RESET}"

# 3. Harvest: Turning Code into a Reusable Skill
step 3 "Harvesting Infrastructure as Skill"
# Dave harvests this script so he never has to write it again.

"$JCAPY_BIN" harvest \
    --doc provision_k8s.sh \
    --name "Provision K8s Cluster" \
    --desc "Standard hardened K3s cluster provisioner (Grade A)" \
    --grade A \
    --yes \
    --force

# 4. Verify the Skill Exists
step 4 "Verifying Knowledge Base"
# We should see the new skill under 'devops' or similar
"$JCAPY_BIN" list

# 5. Simulate Reuse (The Payoff)
# Dave gets paged at 3AM to provision a new cluster.
# Instead of SSHing and typing commands, he applies his refined skill.
step 5 "Applying Skill to Production Target (Simulation)"
"$JCAPY_BIN" apply "provision_k8s_cluster" --dry-run
# Note: In a real scenario, this would execute the script. --dry-run shows intent.

echo -e "\n${GREEN}🎉 Use Case Complete: Dave saved 2 hours of work.${RESET}"
