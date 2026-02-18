#!/bin/bash
set -e

# jcapy Release Automation (Complete Edition)
# Usage: ./scripts/publish.sh
#
# Features:
# - First-time GitHub repo setup
# - Pre-commit pending changes
# - Version bump (patch/minor/major)
# - Git tag + push
# - Homebrew tap update

echo "🚀 jcapy Release Protocol"
echo "================================"

cd "$(dirname "$0")/.."
REPO_NAME="homebrew-JCapy"
GITHUB_USER="ponli550"

# ==========================================
# PHASE 0: First-Time Setup Check
# ==========================================

# Check if gh CLI is available (optional but recommended)
HAS_GH=false
if command -v gh &> /dev/null; then
    HAS_GH=true
fi

# Check if remote exists
if ! git remote get-url origin &> /dev/null; then
    echo "⚠️  No remote 'origin' configured."
    echo ""

    if $HAS_GH; then
        echo "🔧 GitHub CLI detected. Setting up..."

        # Check if repo exists on GitHub
        if gh repo view "$GITHUB_USER/$REPO_NAME" &> /dev/null; then
            echo "📦 Found existing repo: $GITHUB_USER/$REPO_NAME"
        else
            echo "📦 Creating GitHub repo: $GITHUB_USER/$REPO_NAME"
            read -p "❓ Create as (1) Public or (2) Private? [1]: " -n 1 -r
            echo

            VISIBILITY="--public"
            if [[ $REPLY == "2" ]]; then
                VISIBILITY="--private"
            fi

            gh repo create "$GITHUB_USER/$REPO_NAME" $VISIBILITY --source=. --remote=origin
            echo "✅ Repository created!"
        fi
    else
        echo "💡 Install GitHub CLI for automatic repo creation: brew install gh"
        read -p "❓ Enter remote URL (e.g., https://github.com/$GITHUB_USER/$REPO_NAME.git): " REMOTE_URL

        if [[ -z "$REMOTE_URL" ]]; then
            REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
        fi

        git remote add origin "$REMOTE_URL"
        echo "✅ Remote 'origin' added: $REMOTE_URL"
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

# Check if we have any pushable commits
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
# PHASE 5: Homebrew Update (Optional)
# ==========================================

echo ""
read -p "🍺 Update Homebrew tap? (y/n) [y]: " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "🍺 Calculating SHA256 for Homebrew..."
    URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$NEW_VERSION.tar.gz"
    echo "   Waiting for GitHub to generate tarball..."
    sleep 5

    SHA=$(curl -sL "$URL" | shasum -a 256 | cut -d ' ' -f 1)
    echo "   SHA256: $SHA"

    TAP_REPO="https://github.com/$GITHUB_USER/homebrew-$REPO_NAME.git"
    TEMP_DIR="/tmp/jcapy-homebrew-release-$(date +%s)"

    echo "🍺 Updating Homebrew Tap ($TAP_REPO)..."
    git clone "$TAP_REPO" "$TEMP_DIR" 2>/dev/null || {
        echo "⚠️  Could not clone tap repo. Manual update required."
        echo "   URL: $URL"
        echo "   SHA256: $SHA"
        echo ""
        echo "🎉 Release Complete (Homebrew skipped)!"
        exit 0
    }

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
        git config user.email "nazrijz336@gmail.com"
        git config user.name "JCapy Release Bot"
        git add .
        git commit -m "Update jcapy to v$NEW_VERSION"
        git push origin main
        cd - > /dev/null

        echo "✅ Homebrew Tap Updated!"
    else
        echo "❌ Could not find jcapy.rb in cloned tap."
    fi

    rm -rf "$TEMP_DIR"
fi

echo ""
echo "🎉 Release Complete!"
echo "================================"
echo "  Version: v$NEW_VERSION"
echo "  GitHub:  https://github.com/$GITHUB_USER/$REPO_NAME"
echo "  Install: pipx install git+https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
