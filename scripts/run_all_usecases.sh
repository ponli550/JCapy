#!/bin/bash
set -e

# JCapy Master Demo: "The Universal Knowledge Harvester"
# Runs all 10 Role-Based Use Cases sequentially.

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHOWCASE_DIR="$PROJECT_ROOT/showcase"

echo -e "${CYAN}🚀 Starting JCapy Master Demo: 10 Roles, 1 Tool.${RESET}"
echo -e "${YELLOW}Goal: Verify 'Init -> Harvest -> Apply' workflow across all domains.${RESET}\n"

# Array of use cases (Folder Name | Display Name)
declare -a usecases=(
    "01-backend-api|Backend API Architect"
    "02-frontend-ui|Frontend UI Sprinter"
    "03-data-science|Data Science Model Trainer"
    "04-security|Security Paranoiac"
    "05-qa|QA Bug Hunter"
    "06-sre|SRE Firefighter"
    "07-mobile|Mobile App Builder"
    "08-dba|DBA Data Guardian"
    "09-tech-writer|Tech Writer Wizard"
    "10-product-manager|Product Manager Visionary"
)

# Results tracking
declare -a results
total=${#usecases[@]}
passed=0

for entry in "${usecases[@]}"; do
    IFS="|" read -r folder name <<< "$entry"
    script_path="$SHOWCASE_DIR/$folder/usecase.sh"

    echo -e "${CYAN}▶ Running Scenario: $name${RESET}"
    echo -e "  Script: $script_path"

    if [ -f "$script_path" ]; then
        # Execute in subshell to isolate directory changes
        if (bash "$script_path"); then
            echo -e "${GREEN}✔ Success: $name${RESET}\n"
            results+=("✔ $name")
            ((passed++))
        else
            echo -e "${RED}✘ Failed: $name${RESET}\n"
            results+=("✘ $name")
            # Continue even on failure? Yes, for demo purposes usually better to fail fast, but for verification maybe continue.
            # set -e checks exit code, so if the subshell fails, this script will fail unless we handle it.
            # But usecase scripts have set -e.
            # Let's stop on failure to debug.
            echo "Stopping execution due to failure."
            exit 1
        fi
    else
        echo -e "${RED}✘ Error: Script not found: $script_path${RESET}"
        exit 1
    fi
    sleep 1
done

# Summary Table
echo -e "${CYAN}==========================================${RESET}"
echo -e "${CYAN}       JCapy Master Demo Summary          ${RESET}"
echo -e "${CYAN}==========================================${RESET}"
for result in "${results[@]}"; do
    echo -e "$result"
done
echo -e "${CYAN}------------------------------------------${RESET}"

if [ $passed -eq $total ]; then
    echo -e "${GREEN}🎉 All $total Scenarios Verified! JCapy is Ready.${RESET}"
    exit 0
else
    echo -e "${RED}⚠️  Only $passed/$total Scenarios Passed.${RESET}"
    exit 1
fi
