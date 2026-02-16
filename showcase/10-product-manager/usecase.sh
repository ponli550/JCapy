#!/bin/bash
set -e

# Role: Product Manager ("The Visionary")
# Goal: Standardize feature requirements.

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

echo -e "${CYAN}🚀 Scenario: The Visionary${RESET}"
echo -e "PM: 'Focus on the problem, not the solution.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Product Workspace"
"$JCAPY_BIN" init --grade B

step 2 "Drafting PRD Template"
cat <<EOF > PRD_TEMPLATE.md
# Product Requirement Document (PRD)

## 1. Context
*Why are we building this?*

## 2. User Stories
- As a [User], I want to [Action], so that [Benefit].

## 3. Success Metrics
- [ ] Metric 1
- [ ] Metric 2

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
|      |            |
EOF
echo -e "${GREEN}✔ Created PRD_TEMPLATE.md${RESET}"

step 3 "Harvesting PRD Standard"
"$JCAPY_BIN" harvest \
    --doc PRD_TEMPLATE.md \
    --name "PRD Standard Template" \
    --desc "Unified product requirement document" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Applying PRD to New Feature"
"$JCAPY_BIN" apply "prd_standard_template" --dry-run
