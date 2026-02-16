#!/bin/bash
set -e

# Role: Mobile Developer ("The App Builder")
# Goal: Standardize React Native initialization.

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

echo -e "${CYAN}🚀 Scenario: The App Builder${RESET}"
echo -e "Mobile Dev: 'Simulator builds taking too long? Use the CLI.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Mobile Workspace"
"$JCAPY_BIN" init --grade B

step 2 "Drafting Fastlane Config"
cat <<EOF > Fastfile
default_platform(:ios)

platform :ios do
  desc "Push a new beta build to TestFlight"
  lane :beta do
    increment_build_number(xcodeproj: "App.xcodeproj")
    build_app(workspace: "App.xcworkspace", scheme: "App")
    upload_to_testflight
  end
end
EOF
echo -e "${GREEN}✔ Created Fastfile${RESET}"

step 3 "Harvesting CD Pipeline"
"$JCAPY_BIN" harvest \
    --doc Fastfile \
    --name "Fastlane iOS Beta" \
    --desc "Automated TestFlight deployment" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Deploying Pipeline to New App"
"$JCAPY_BIN" apply "fastlane_ios_beta" --dry-run
