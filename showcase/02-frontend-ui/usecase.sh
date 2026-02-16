#!/bin/bash
set -e

# Role: Frontend Developer ("The UI Sprinter")
# Goal: Create a reusable component library.

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

echo -e "${CYAN}🚀 Scenario: The UI Sprinter${RESET}"
echo -e "Dev: 'Consistent buttons are key to a consistent soul.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing UI Project"
"$JCAPY_BIN" init --grade B

step 2 "Drafting Golden Button Component"
cat <<EOF > Button.tsx
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({ label, onClick, variant = 'primary' }) => {
  return (
    <button
      className={\`btn btn-\${variant}\`}
      onClick={onClick}
    >
      {label}
    </button>
  );
};
EOF
echo -e "${GREEN}✔ Created Button.tsx${RESET}"

step 3 "Harvesting UI Component"
"$JCAPY_BIN" harvest \
    --doc Button.tsx \
    --name "React Button Component" \
    --desc "TypeScript React Button with variants" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Reusing Component"
"$JCAPY_BIN" apply "react_button_component" --dry-run
