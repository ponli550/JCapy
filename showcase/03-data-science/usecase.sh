#!/bin/bash
set -e

# Role: Data Scientist ("The Model Trainer")
# Goal: Standardize model training pipelines.

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

echo -e "${CYAN}🚀 Scenario: The Model Trainer${RESET}"
echo -e "Scientist: 'It works on my machine... and now yours too.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing Lab Environment"
"$JCAPY_BIN" init --grade B

step 2 "Creating Training Pipeline"
cat <<EOF > train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load Data
df = pd.read_csv('data.csv')
X = df.drop('target', axis=1)
y = df['target']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Evaluate
preds = clf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, preds)}")

# Save
joblib.dump(clf, 'model.pkl')
EOF
echo -e "${GREEN}✔ Created train_model.py${RESET}"

step 3 "Harvesting Training Pipeline"
"$JCAPY_BIN" harvest \
    --doc train_model.py \
    --name "Sklearn Training Pipeline" \
    --desc "Standard Random Forest training script" \
    --grade B \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Deploying Pipeline to New Experiment"
"$JCAPY_BIN" apply "sklearn_training_pipeline" --dry-run
