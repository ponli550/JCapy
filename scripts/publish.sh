#!/bin/bash
set -e

# jcapy Combined Release Automation
# Usage: ./scripts/publish.sh
#
# Features:
# - Auto-creates virtual environment for PyPI builds
# - Pre-commit pending changes
# - Version bump (patch/minor/major)
# - Git tag + push
# - Choose: Homebrew / PyPI / Both

echo "🚀 jcapy Release Protocol (Combined)"
echo "======================================"

cd "$(dirname "$0")/.."
REPO_NAME="JCapy"
GITHUB_USER="ponli550"
HOMEBREW_TAP_REPO="homebrew-JCapy"

# ==========================================
# PHASE 0: Virtual Environment Setup (for PyPI)
# ==========================================

setup_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo ""
        echo "🔧 Setting up virtual environment for PyPI build..."

        if [ -d "venv" ]; then
            source venv/bin/activate
            echo "   ✔ Activated existing venv"
        else
            python3 -m venv venv
            source venv/bin/activate
            pip install --quiet --upgrade pip build twine
            echo "   ✔ Created and configured venv"
        fi
    fi
}

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
# PHASE 5: Select Distribution Targets
# ==========================================

echo ""
echo "Select Distribution Targets:"
echo "  1) 🍺 Homebrew only"
echo "  2) 🐍 PyPI only"
echo "  3) 🚀 Both (Homebrew + PyPI)"
echo "  0) Skip distribution (code release only)"
read -p "Choice (0-3): " -n 1 -r
echo

DO_HOMEBREW=false
DO_PYPI=false

if [[ $REPLY == "1" ]]; then
    DO_HOMEBREW=true
elif [[ $REPLY == "2" ]]; then
    DO_PYPI=true
elif [[ $REPLY == "3" ]]; then
    DO_HOMEBREW=true
    DO_PYPI=true
elif [[ $REPLY == "0" ]]; then
    echo "⏭️  Skipping distribution."
fi

# ==========================================
# PHASE 6a: Homebrew Update
# ==========================================

if $DO_HOMEBREW; then
    echo ""
    echo "🍺 Updating Homebrew Tap..."

    URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$NEW_VERSION.tar.gz"
    echo "   Waiting for GitHub to generate tarball..."
    sleep 5

    SHA=$(curl -sL "$URL" | shasum -a 256 | cut -d ' ' -f 1)
    echo "   SHA256: $SHA"

    TAP_REPO="https://github.com/$GITHUB_USER/$HOMEBREW_TAP_REPO.git"
    TEMP_DIR="/tmp/jcapy-homebrew-release-$(date +%s)"

    git clone "$TAP_REPO" "$TEMP_DIR" 2>/dev/null || {
        echo "⚠️  Could not clone tap repo. Manual update required."
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

            echo "✅ Homebrew Tap Updated!"
        fi

        rm -rf "$TEMP_DIR"
    fi
fi

# ==========================================
# PHASE 6b: PyPI Upload
# ==========================================

if $DO_PYPI; then
    # Ensure venv is active for PyPI operations
    setup_venv

    echo ""
    echo "🐍 Building for PyPI..."

    # Clean old builds
    rm -rf dist/ build/ *.egg-info src/*.egg-info

    # Build
    python3 -m pip install --quiet --upgrade build
    python3 -m build

    echo "✅ Built:"
    ls -la dist/

    echo ""
    echo "Select PyPI Target:"
    echo "  1) TestPyPI (recommended for first release)"
    echo "  2) Production PyPI"
    read -p "Choice (1-2): " -n 1 -r
    echo

    python3 -m pip install --quiet --upgrade twine

    if [[ $REPLY == "1" ]]; then
        echo "🚀 Uploading to TestPyPI..."
        python3 -m twine upload --repository testpypi dist/*
        echo "✅ Uploaded to TestPyPI!"
        echo "   Test: pip install --index-url https://test.pypi.org/simple/ --no-deps jcapy"
    elif [[ $REPLY == "2" ]]; then
        echo "🚀 Uploading to Production PyPI..."
        python3 -m twine upload dist/*
        echo "✅ Uploaded to PyPI!"
        echo "   Install: pip install jcapy"
    fi
fi

echo ""
echo "🎉 Release Complete!"
echo "======================================"
echo "  Version: v$NEW_VERSION"
echo "  GitHub:  https://github.com/$GITHUB_USER/$REPO_NAME"
if $DO_HOMEBREW; then
    echo "  Homebrew: brew install $GITHUB_USER/jcapy/jcapy"
fi
if $DO_PYPI; then
    echo "  PyPI: pip install jcapy"
fi
echo ""
