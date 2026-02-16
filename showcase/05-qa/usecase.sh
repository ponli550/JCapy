#!/bin/bash
set -e

# Role: QA Engineer ("The Bug Hunter")
# Goal: Run regression tests with a single command.

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

echo -e "${CYAN}🚀 Scenario: The Bug Hunter${RESET}"
echo -e "QA: 'If it ain't tested, it's broken.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Test Suite"
"$JCAPY_BIN" init --grade B

step 2 "Drafting E2E Test Suite Config"
cat <<EOF > cypress.config.js
const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});
# Simulating a test file too
console.log("Cypress E2E Config Generated");
EOF
echo -e "${GREEN}✔ Created cypress.config.js${RESET}"

step 3 "Harvesting Test Infrastructure"
"$JCAPY_BIN" harvest \
    --doc cypress.config.js \
    --name "Cypress E2E Setup" \
    --desc "Standard Cypress configuration for E2E testing" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Injecting Tests into New Project"
"$JCAPY_BIN" apply "cypress_e2e_setup" --dry-run
