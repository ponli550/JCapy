#!/bin/bash
set -e

# jcapy PyPI Release Automation
# Usage: ./scripts/publishPip.sh
#
# Features:
# - Pre-commit pending changes
# - Version bump (patch/minor/major)
# - Git tag + push
# - Build wheel + sdist
# - Upload to PyPI (TestPyPI or Production)

echo "🐍 jcapy PyPI Release Protocol"
echo "================================"

cd "$(dirname "$0")/.."
GITHUB_USER="ponli550"
REPO_NAME="JCapy"

# ==========================================
# PHASE 0: Check PyPI Credentials
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
    echo "   ✔ Found TWINE_PASSWORD environment variable"
fi

if ! $HAS_PYPIRC && ! $HAS_ENV_TOKEN; then
    echo "⚠️  No PyPI credentials found!"
    echo ""
    echo "Options:"
    echo "  1. Create ~/.pypirc with your API token"
    echo "  2. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<your-token>"
    echo ""
    read -p "❓ Continue anyway? (will prompt for token) [y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
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

    read -p "❓ Commit these changes before release? (y/n) [y]: " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        read -p "💬 Commit message: " COMMIT_MSG

        if [[ -z "$COMMIT_MSG" ]]; then
            COMMIT_MSG="Pre-release commit"
        fi

        git add .
        git commit -m "$COMMIT_MSG"
        echo "✅ Changes committed."
    fi
fi

# ==========================================
# PHASE 2: First Push (if needed)
# ==========================================

UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")

if [[ -z "$UPSTREAM" ]]; then
    echo ""
    echo "🔄 First-time push to origin/main..."
    git push -u origin main
    echo "✅ Initial push complete."
fi

# ==========================================
# PHASE 3: Version Bump
# ==========================================

VERSION_FILE="src/jcapy/utils/updates.py"
CURRENT_VERSION=$(grep 'VERSION = ' "$VERSION_FILE" | cut -d '"' -f 2)
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
        echo "Invalid choice. Aborting."
        exit 1
    fi

    echo "🎯 Target Version: $NEW_VERSION"

    read -p "❓ Proceed with release v$NEW_VERSION? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi

    # Update version files
    echo "📝 Updating version files..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
        sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
    else
        sed -i "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
        sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
    fi
    echo "✅ Updated to $NEW_VERSION"

    # Commit version bump
    if [[ -n $(git status -s) ]]; then
        git add .
        git commit -m "Release v$NEW_VERSION"
    fi
fi

# ==========================================
# PHASE 4: Tag & Push
# ==========================================

# Check if tag already exists
if git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
    echo "⚠️  Tag v$NEW_VERSION already exists. Skipping tag creation."
else
    echo "🏷️  Tagging v$NEW_VERSION..."
    git tag "v$NEW_VERSION"
fi

echo "⬆️  Pushing to origin..."
git push origin main
git push origin "v$NEW_VERSION" 2>/dev/null || echo "   (Tag already pushed)"
echo "✅ Code released to GitHub."

# ==========================================
# PHASE 5: Build Distribution
# ==========================================

echo ""
echo "🔨 Building distribution packages..."

# Clean old builds
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Build wheel and sdist
python3 -m pip install --quiet --upgrade build
python3 -m build

echo "✅ Built:"
ls -la dist/

# ==========================================
# PHASE 6: Upload to PyPI
# ==========================================

echo ""
echo "Select PyPI Target:"
echo "  1) TestPyPI (recommended for first release)"
echo "  2) Production PyPI"
echo "  0) Skip upload (build only)"
read -p "Choice (0-2): " -n 1 -r
echo

if [[ $REPLY == "0" ]]; then
    echo "⏭️  Skipping upload."
elif [[ $REPLY == "1" ]]; then
    echo "🚀 Uploading to TestPyPI..."
    python3 -m pip install --quiet --upgrade twine
    python3 -m twine upload --repository testpypi dist/*
    echo ""
    echo "✅ Uploaded to TestPyPI!"
    echo "   Test: pip install --index-url https://test.pypi.org/simple/ --no-deps jcapy"
elif [[ $REPLY == "2" ]]; then
    echo "🚀 Uploading to Production PyPI..."
    python3 -m pip install --quiet --upgrade twine
    python3 -m twine upload dist/*
    echo ""
    echo "✅ Uploaded to PyPI!"
    echo "   Install: pip install jcapy"
else
    echo "Invalid choice. Skipping upload."
fi

echo ""
echo "🎉 PyPI Release Complete!"
echo "================================"
echo "  Version: v$NEW_VERSION"
echo "  GitHub:  https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
