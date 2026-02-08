#!/bin/bash
set -e

# jcapy Release Automation (Modular Version)
# Usage: ./scripts/publish.sh

echo "🚀 jcapy Release Protocol"
echo "--------------------------------"

cd "$(dirname "$0")/.."

# 1. Extract Current Version from updates.py
VERSION_FILE="src/jcapy/utils/updates.py"
CURRENT_VERSION=$(grep 'VERSION = ' "$VERSION_FILE" | cut -d '"' -f 2)
echo "📦 Current Version: $CURRENT_VERSION"

# 2. Select Bump Type
echo "Select Release Type:"
echo "  1) Patch (x.x.+1) - Bug fixes"
echo "  2) Minor (x.+1.0) - New features"
echo "  3) Major (+1.0.0) - Breaking changes"
read -p "Choice (1-3): " -n 1 -r
echo

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

# Safety Check
read -p "❓ Proceed with release v$NEW_VERSION? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# 3. Update Version Files
echo "📝 Updating version files..."

# Update updates.py
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
    sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
else
    sed -i "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$VERSION_FILE"
    sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "pyproject.toml"
fi
echo "✅ Updated to $NEW_VERSION"

# 4. Git Commit & Tag
if [[ -n $(git status -s) ]]; then
    git add .
    git commit -m "Release v$NEW_VERSION"
fi

echo "🏷️  Tagging v$NEW_VERSION..."
git tag "v$NEW_VERSION"

echo "⬆️  Pushing to origin..."
git push origin main
git push origin "v$NEW_VERSION"
echo "✅ Code released to GitHub."

# 5. Homebrew Update Calculation
echo "🍺 Calculating SHA256 for Homebrew..."
URL="https://github.com/ponli550/JCapy/archive/refs/tags/v$NEW_VERSION.tar.gz"
echo "   Waiting for GitHub to generate tarball..."
sleep 5

# Download and calc hash
SHA=$(curl -sL "$URL" | shasum -a 256 | cut -d ' ' -f 1)
echo "   SHA256: $SHA"

# 6. Automate Homebrew Tap Update
TAP_REPO="https://github.com/ponli550/homebrew-JCapy.git"
TEMP_DIR="/tmp/jcapy-homebrew-release-$(date +%s)"

echo "🍺 Updating Homebrew Tap ($TAP_REPO)..."
git clone "$TAP_REPO" "$TEMP_DIR" 2>/dev/null || {
    echo "⚠️  Could not clone tap repo. Manual update required."
    echo "   URL: $URL"
    echo "   SHA256: $SHA"
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
    git config user.email "jcapy-bot@ponli550.com"
    git config user.name "JCapy Release Bot"
    git add .
    git commit -m "Update jcapy to v$NEW_VERSION"
    git push origin main
    cd - > /dev/null

    echo "✅ Homebrew Tap Updated!"
else
    echo "❌ Could not find jcapy.rb in cloned tap."
fi

# Cleanup
rm -rf "$TEMP_DIR"
echo "🎉 Release Complete!"
