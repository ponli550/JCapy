#!/bin/bash
set -e

# Role: DBA ("The Data Guardian")
# Goal: Automate PostgreSQL backups.

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

echo -e "${CYAN}🚀 Scenario: The Data Guardian${RESET}"
echo -e "DBA: 'Data lost is trust lost.'"

DEMO_DIR=$(mktemp -d)
trap "rm -rf $DEMO_DIR" EXIT
cd "$DEMO_DIR"

step 1 "Initializing DB Workspace"
"$JCAPY_BIN" init --grade A

step 2 "Drafting Backup Script"
cat <<EOF > backup_postgres.sh
#!/bin/bash
DB_NAME="production_db"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_\${DB_NAME}_\${DATE}.sql"

echo "💾 Backing up \${DB_NAME} to \${BACKUP_FILE}..."
# pg_dump \$DB_NAME > \$BACKUP_FILE
echo "✅ Backup Complete."

echo "☁️  Uploading to S3..."
# aws s3 cp \$BACKUP_FILE s3://my-backups/
echo "✅ Upload Complete."
EOF
chmod +x backup_postgres.sh
echo -e "${GREEN}✔ Created backup_postgres.sh${RESET}"

step 3 "Harvesting Backup Routine"
"$JCAPY_BIN" harvest \
    --doc backup_postgres.sh \
    --name "Postgres Backup Strategy" \
    --desc "Automated S3 backup script" \
    --grade A \
    --yes \
    --force

step 4 "Verification"
"$JCAPY_BIN" list

step 5 "Applying Backup to Staging"
"$JCAPY_BIN" apply "postgres_backup_strategy" --dry-run
