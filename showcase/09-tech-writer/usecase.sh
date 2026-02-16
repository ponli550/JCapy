#!/bin/bash
set -e

# Role: Technical Writer ("The Documentation Wizard")
# Goal: Standardize documentation structure.

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

echo -e "${CYAN}🚀 Scenario: The Documentation Wizard${RESET}"
echo -e "Writer: 'Code is prose. Treat it as such.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Docs Project"
"$JCAPY_BIN" init --grade B

step 2 "Drafting MkDocs Config"
cat <<EOF > mkdocs.yml
site_name: Project Documentation
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo

nav:
  - Home: index.md
  - API Guide: api.md
  - Contributing: contributing.md

plugins:
  - search
EOF
echo -e "${GREEN}✔ Created mkdocs.yml${RESET}"

step 3 "Harvesting Docs Structure"
"$JCAPY_BIN" harvest \
    --doc mkdocs.yml \
    --name "Material Docs Setup" \
    --desc "MkDocs Material theme configuration" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Applying Docs Config to New Repo"
"$JCAPY_BIN" apply "material_docs_setup" --dry-run
