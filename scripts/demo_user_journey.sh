#!/bin/bash
set -e

# Function for visual hierarchy
function step() {
    sleep 1 # Pause for dramatic effect/readability
    echo -e "\n${CYAN}STEP $1: $2${RESET}"
    echo -e "${YELLOW}------------------------------------------${RESET}"
}

# Determine local jcapy path
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JCAPY_BIN="$PROJECT_ROOT/.venv/bin/jcapy"

echo -e "${YELLOW}🔧 Using JCapy at: ${JCAPY_BIN}${RESET}"

# Create a temporary directory for the demo
DEMO_DIR=$(mktemp -d)
echo -e "${YELLOW}📂 Created temporary directory: ${DEMO_DIR}${RESET}"

# Ensure we cleanup on exit
trap "rm -rf $DEMO_DIR" EXIT

cd "$DEMO_DIR"

# 1. Initialize Project
step 1 "Initializing Project (jcapy init)"
"$JCAPY_BIN" init --grade B

# Verify initialization
if [ -f ".jcapyrc" ] && [ -f "package.json" ]; then
    echo -e "${GREEN}✅ Project initialized successfully.${RESET}"
else
    echo -e "${RED}❌ Project initialization failed.${RESET}"
    exit 1
fi

# 2. Create a dummy script to harvest
step 2 "Creating a dummy script for harvesting"
cat <<EOF > deploy_demo.sh
#!/bin/bash
echo "Deploying demo application..."
docker build -t demo-app .
docker run -d -p 8080:80 demo-app
echo "Deployment complete."
EOF
chmod +x deploy_demo.sh
echo -e "${GREEN}✅ Created deploy_demo.sh${RESET}"

# 3. Harvest the script as a skill
step 3 "Harvesting Skill (jcapy harvest)"
# Using new headless mode flags + force to avoid overwrite prompt

"$JCAPY_BIN" harvest \
    --doc deploy_demo.sh \
    --name "Demo Deploy" \
    --desc "A demo deployment script (Headless)" \
    --grade B \
    --yes \
    --force

# 4. List Skills to verify
step 4 "Listing Skills (jcapy list)"
"$JCAPY_BIN" list

# 5. Run Doctor to check health
step 5 "System Health Check (jcapy doctor)"
"$JCAPY_BIN" doctor

# 6. Switch Persona
step 6 "Switching Persona (jcapy persona)"
"$JCAPY_BIN" persona programmer

echo -e "\n${GREEN}🎉 End-to-End User Journey Completed Successfully!${RESET}"
