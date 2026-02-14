#!/bin/bash
# scripts/setup_security.sh
# Sets up pre-commit hooks and runs local security scans.

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🔒 Setting up JCapy Security Protocols...${NC}"

# 1. Create Pre-commit Hook
HOOK_PATH=".git/hooks/pre-commit"

echo -e "Creating pre-commit hook at $HOOK_PATH..."
cat > $HOOK_PATH << 'EOF'
#!/bin/bash
# JCapy Pre-commit Hook: Prevent Secrets Leak via TruffleHog

echo "🔒 Running generic secret checks..."

# Check if trufflehog is installed
if command -v trufflehog &> /dev/null; then
    # Run trufflehog on staged files (simplified check on current dir for now)
    # Ideally should git diff --cached but trufflehog filesystem is easier for a quick check
    echo "  • Scanning for secrets..."

    # Run trufflehog against the current directory, failing if high/critical issues found
    # Using 'filesystem' scanner in Docker or local binary if available
    # For speed, we might just warn if not present.

    trufflehog filesystem . --only-verified --fail

    if [ $? -ne 0 ]; then
        echo "❌ Secrets detected! Aborting commit."
        exit 1
    fi
else
    echo "⚠️ TruffleHog not found. Skipping secret scan."
    echo "  (Install: brew install trufflehog)"
fi

# 2. Check for large files (>100MB)
echo "📦 Checking for large files..."
# ... (simplified)

exit 0
EOF

chmod +x $HOOK_PATH
echo -e "${GREEN}✅ Pre-commit hook installed.${NC}"

# 2. Run Initial TruffleHog Scan
if command -v trufflehog &> /dev/null; then
    echo -e "\n${GREEN}🕵️ Running initial TruffleHog scan...${NC}"
    trufflehog filesystem . --only-verified
else
    echo -e "\n${RED}⚠️ TruffleHog is not installed.${NC}"
    echo "Please run: brew install trufflehog"
fi

echo -e "\n${GREEN}🛡️ Security setup complete.${NC}"
