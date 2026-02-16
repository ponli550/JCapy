#!/bin/bash
set -e

# Role: Backend Developer ("The API Architect")
# Goal: Rapidly scaffold a microservice foundation.

# ANSI Colors
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

echo -e "${CYAN}🚀 Scenario: The API Architect${RESET}"
echo -e "Dev: 'Microservices should be easy, right?'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Backend Service"
"$JCAPY_BIN" init --grade B

step 2 "Creating FastAPI Scaffold"
cat <<EOF > api_service.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
EOF
echo -e "${GREEN}✔ Created api_service.py${RESET}"

step 3 "Harvesting API Template"
"$JCAPY_BIN" harvest \
    --doc api_service.py \
    --name "FastAPI Service Template" \
    --desc "Basic FastAPI scaffold with auto-docs" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Applying to New Microservice"
"$JCAPY_BIN" apply "fastapi_service_template" --dry-run
