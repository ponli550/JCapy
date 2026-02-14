#!/bin/bash
set -e

# ============================================================================
# jcapy Combined Release Automation (Secure Edition)
# ============================================================================
# Usage: ./scripts/publish.sh [OPTIONS]
#
# Options:
#   --dry-run    Preview all commands without executing
#   --force      Skip confirmation prompts (use with caution)
#
# Flow: Pip-First, Homebrew Opt-In
#   Phase 0a: Virtual Environment Setup (upfront)
#   Phase 0b: Security Checks (branch, clean tree, remote, version)
#   Phase 0c: PyPI Credential Check (fail fast)
#   Phase 1:  Pre-Commit Pending Changes
#   Phase 2:  Version Bump
#   Phase 3:  Tag & Push
#   Phase 4:  PyPI Build & Upload (default path)
#   Phase 5:  Homebrew Update (opt-in)
#   Phase 6:  Summary
# ============================================================================

echo "🚀 jcapy Release Protocol (Secure Edition)"
echo "============================================"

cd "$(dirname "$0")/.."

# ==========================================
# CONFIGURATION
# ==========================================

REPO_NAME="JCapy"
GITHUB_USER="ponli550"
HOMEBREW_TAP_REPO="homebrew-jcapy"
VERSION_FILE="src/jcapy/utils/updates.py"
ALLOWED_BRANCH="main"

# ==========================================
# PARSE ARGUMENTS
# ==========================================

DRY_RUN=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            echo "⚠️  DRY-RUN MODE: No changes will be made"
            echo ""
            ;;
        --force)
            FORCE=true
            echo "⚠️  FORCE MODE: Skipping confirmation prompts"
            echo ""
            ;;
    esac
done

# ==========================================
# HELPER FUNCTIONS
# ==========================================

run_cmd() {
    if $DRY_RUN; then
        echo "   [DRY-RUN] $*"
    else
        "$@"
    fi
}

confirm() {
    if $FORCE; then
        return 0
    fi
    local message="$1"
    read -p "❓ $message (y/n) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

error_exit() {
    echo "❌ ERROR: $1"
    exit 1
}

warning() {
    echo "⚠️  WARNING: $1"
}

success() {
    echo "✅ $1"
}

# ==========================================
# PHASE 0a: Virtual Environment Setup
# ==========================================

echo ""
echo "🔧 Setting up virtual environment..."

if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "   ✔ Activated existing venv"
    else
        if $DRY_RUN; then
            echo "   [DRY-RUN] Would create and configure venv"
        else
            python3 -m venv venv
            source venv/bin/activate
            pip install --quiet --upgrade pip build twine
            echo "   ✔ Created and configured venv"
        fi
    fi
else
    echo "   ✔ Virtual environment already active: $VIRTUAL_ENV"
fi

# ==========================================
# PHASE 0b: SECURITY CHECKS
# ==========================================

echo ""
echo "🔒 Running Security Checks..."
echo "------------------------------"

# Check 1: Branch Protection
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "$ALLOWED_BRANCH" ]]; then
    error_exit "Releases must be made from '$ALLOWED_BRANCH' branch. Currently on '$CURRENT_BRANCH'."
fi
success "Branch check passed: on '$ALLOWED_BRANCH'"

# Check 2: Clean Working Tree (warn only, don't block — pre-commit handles later)
if [[ -n $(git status -s) ]]; then
    warning "Uncommitted changes detected (will be handled in pre-commit phase)."
else
    success "Working tree is clean"
fi

# Check 3: GitHub Remote Access
if ! git ls-remote origin &>/dev/null; then
    error_exit "Cannot connect to GitHub remote 'origin'. Check your credentials."
fi
success "GitHub remote accessible"

# Check 4: Current Version Sanity
CURRENT_VERSION=$(grep 'VERSION = ' "$VERSION_FILE" | cut -d '"' -f 2)
PYPROJECT_VERSION=$(grep '^version = ' "pyproject.toml" | cut -d '"' -f 2)

if [[ "$CURRENT_VERSION" != "$PYPROJECT_VERSION" ]]; then
    warning "Version mismatch detected!"
    echo "   updates.py:    $CURRENT_VERSION"
    echo "   pyproject.toml: $PYPROJECT_VERSION"
    if ! confirm "Continue anyway?"; then
        error_exit "Aborted due to version mismatch."
    fi
else
    success "Version files in sync: $CURRENT_VERSION"
fi

echo ""
echo "🔒 All security checks passed!"

# ==========================================
# PHASE 0c: PyPI Credential Check (Fail Fast)
# ==========================================

echo ""
echo "🔐 Checking PyPI credentials..."

HAS_PYPIRC=false
HAS_ENV_TOKEN=false

if [ -f ~/.pypirc ]; then
    HAS_PYPIRC=true
    echo "   ✔ Found ~/.pypirc"
fi

if [ -n "$TWINE_PASSWORD" ]; then
    HAS_ENV_TOKEN=true
    echo "   ✔ Found TWINE_PASSWORD"
fi

if ! $HAS_PYPIRC && ! $HAS_ENV_TOKEN; then
    warning "No stored PyPI credentials found."
    echo "   Options:"
    echo "     1. Create ~/.pypirc with your API token"
    echo "     2. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<your-token>"
    echo ""
    if ! confirm "Continue anyway? (will prompt for token during upload)"; then
        error_exit "Aborted — set up PyPI credentials first."
    fi
fi

# ==========================================
# PHASE 1: Pre-Commit Pending Changes
# ==========================================

if [[ -n $(git status -s) ]]; then
    echo ""
    echo "📝 Pending changes detected:"
    git status -s
    echo ""

    if confirm "Commit these changes before release?"; then
        if $FORCE; then
            COMMIT_MSG="Pre-release commit"
        else
            read -p "💬 Commit message: " COMMIT_MSG
            if [[ -z "$COMMIT_MSG" ]]; then
                COMMIT_MSG="Pre-release commit"
            fi
        fi

        if $DRY_RUN; then
            echo "   [DRY-RUN] Would commit: $COMMIT_MSG"
        else
            git add .
            git commit -m "$COMMIT_MSG"
            success "Changes committed."
        fi
    fi
fi

# ==========================================
# PHASE 2: Version Bump
# ==========================================

echo ""
echo "📦 Current Version: $CURRENT_VERSION"
echo ""
echo "Select Release Type:"
echo "  1) Patch (x.x.+1) - Bug fixes"
echo "  2) Minor (x.+1.0) - New features"
echo "  3) Major (+1.0.0) - Breaking changes"
echo "  0) Skip version bump (just push current)"
read -p "Choice (0-3): " -n 1 -r
echo

if [[ $REPLY == "0" ]]; then
    NEW_VERSION="$CURRENT_VERSION"
    echo "⏭️  Keeping version $NEW_VERSION"
else
    IFS='.' read -r -a parts <<< "$CURRENT_VERSION"
    MAJOR=${parts[0]}
    MINOR=${parts[1]}
    PATCH=${parts[2]}

    if [[ $REPLY == "1" ]]; then
        NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
    elif [[ $REPLY == "2" ]]; then
        NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
    elif [[ $REPLY == "3" ]]; then
        NEW_VERSION="$((MAJOR + 1)).0.0"
    else
        error_exit "Invalid choice."
    fi

    # Version Validation: Check tag doesn't already exist
    if git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
        error_exit "Tag v$NEW_VERSION already exists! Choose a different version."
    fi

    echo "🎯 Target Version: $NEW_VERSION"

    if ! confirm "Proceed with release v$NEW_VERSION?"; then
        error_exit "Aborted by user."
    fi

    # Update version files
    echo "📝 Updating version files..."
    if $DRY_RUN; then
        echo "   [DRY-RUN] Would update VERSION to $NEW_VERSION"
    else
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
            sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
        else
            sed -i "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
            sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
        fi
        success "Updated to $NEW_VERSION"

        # Commit version bump
        if [[ -n $(git status -s) ]]; then
            git add .
            git commit -m "Release v$NEW_VERSION"
        fi
    fi
fi

# ==========================================
# PHASE 3: Tag & Push
# ==========================================

echo ""
echo "🏷️  Creating tag v$NEW_VERSION..."

if $DRY_RUN; then
    echo "   [DRY-RUN] Would create tag v$NEW_VERSION"
    echo "   [DRY-RUN] Would push to origin/main"
else
    if ! git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
        git tag "v$NEW_VERSION"
    fi

    echo "⬆️  Pushing to origin..."
    if ! confirm "Push v$NEW_VERSION to GitHub?"; then
        error_exit "Aborted before push."
    fi

    git push origin main
    git push origin "v$NEW_VERSION" 2>/dev/null || echo "   (Tag already pushed)"
    success "Code released to GitHub."
fi

# ==========================================
# PHASE 4: PyPI Build & Upload
# ==========================================

echo ""
echo "🐍 PyPI Build & Upload"
echo "----------------------"

if $DRY_RUN; then
    echo "   [DRY-RUN] Would clean dist/"
    echo "   [DRY-RUN] Would install/upgrade build tools"
    echo "   [DRY-RUN] Would build wheel + sdist"
    echo "   [DRY-RUN] Would upload to PyPI"
else
    # Clean old builds
    rm -rf dist/ build/ *.egg-info src/*.egg-info

    # Enterprise Split Check
    if [ -d "private" ] || [ -d "pro" ]; then
        echo "⚠️  Enterprise directories detected!"
        if ! confirm "Ensure 'private/' and 'pro/' are excluded from MANIFEST.in. Continue?"; then
             error_exit "Aborted safety check."
        fi
    fi

    # Ensure build tools are available
    pip install --quiet --upgrade build twine

    # Build
    python3 -m build

    echo "✅ Built:"
    ls -la dist/

    echo ""
    echo "Select PyPI Target:"
    echo "  1) TestPyPI (recommended for first release)"
    echo "  2) Production PyPI"
    echo "  0) Skip upload (build only)"
    read -p "Choice (0-2): " -n 1 -r
    echo

    if [[ $REPLY == "0" ]]; then
        echo "⏭️  Skipping upload (built packages saved in dist/)."
    elif [[ $REPLY == "1" ]]; then
        echo "🚀 Uploading to TestPyPI..."
        python3 -m twine upload --repository testpypi dist/*
        success "Uploaded to TestPyPI!"
        echo "   Test: pip install --index-url https://test.pypi.org/simple/ --no-deps jcapy"
    elif [[ $REPLY == "2" ]]; then
        echo "🚀 Uploading to Production PyPI..."
        python3 -m twine upload dist/*
        success "Uploaded to PyPI!"
        echo "   Install: pip install jcapy"
    else
        echo "⚠️  Invalid choice. Skipping upload."
    fi
fi

# ==========================================
# PHASE 5: Homebrew Update (Opt-In)
# ==========================================

echo ""
if confirm "🍺 Also update Homebrew tap?"; then
    echo ""
    echo "🍺 Updating Homebrew Tap..."

    URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$NEW_VERSION.tar.gz"

    if $DRY_RUN; then
        echo "   [DRY-RUN] Would fetch tarball from $URL"
        echo "   [DRY-RUN] Would update $HOMEBREW_TAP_REPO formula"
    else
        echo "   Waiting for GitHub to generate tarball..."
        sleep 5

        SHA=$(curl -sL "$URL" | shasum -a 256 | cut -d ' ' -f 1)
        echo "   SHA256: $SHA"

        TAP_REPO="https://github.com/$GITHUB_USER/$HOMEBREW_TAP_REPO.git"
        TEMP_DIR="/tmp/jcapy-homebrew-release-$(date +%s)"

        git clone "$TAP_REPO" "$TEMP_DIR" 2>/dev/null || {
            warning "Could not clone tap repo. Manual update required."
            echo "   URL: $URL"
            echo "   SHA256: $SHA"
        }

        if [ -d "$TEMP_DIR" ]; then
            FORMULA_PATH="$TEMP_DIR/Formula/jcapy.rb"
            if [ ! -f "$FORMULA_PATH" ]; then
                FORMULA_PATH="$TEMP_DIR/jcapy.rb"
            fi

            if [ -f "$FORMULA_PATH" ]; then
                echo "📝 Updating $FORMULA_PATH..."
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s|url \".*\"|url \"$URL\"|" "$FORMULA_PATH"
                    sed -i '' "s|sha256 \".*\"|sha256 \"$SHA\"|" "$FORMULA_PATH"
                else
                    sed -i "s|url \".*\"|url \"$URL\"|" "$FORMULA_PATH"
                    sed -i "s|sha256 \".*\"|sha256 \"$SHA\"|" "$FORMULA_PATH"
                fi

                cd "$TEMP_DIR"
                git config user.email "jcapy-bot@ponli550.com"
                git config user.name "JCapy Release Bot"
                git add .
                git commit -m "Update jcapy to v$NEW_VERSION"
                git push origin main
                cd - > /dev/null

                success "Homebrew Tap Updated!"
            fi

            rm -rf "$TEMP_DIR"
        fi
    fi
fi

# ==========================================
# PHASE 6: SUMMARY
# ==========================================

echo ""
echo "🎉 Release Complete!"
echo "============================================"
echo "  Version: v$NEW_VERSION"
echo "  GitHub:  https://github.com/$GITHUB_USER/$REPO_NAME"
echo "  PyPI:    pip install jcapy"
if $DRY_RUN; then
    echo ""
    echo "  ⚠️  This was a DRY-RUN. No changes were made."
else
    # Post-Release Cleanup
    echo ""
    echo "🧹 Post-Release Cleanup..."
    echo "   • Re-installing in editable mode for development..."
    pip install -e .
    echo "   ✔ Ready for next dev cycle."
fi
echo ""
