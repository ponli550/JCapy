#!/bin/bash
set -e

# jcapy Development Setup
# Usage: ./scripts/setup.sh

echo "🚀 JCapy Development Setup"
echo "--------------------------------"

# 1. Check Python Version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📦 Python Version: $PYTHON_VERSION"

# 2. Create Virtual Environment (optional)
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created at .venv"
fi

# 3. Activate Virtual Environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# 4. Install in Development Mode
echo "📦 Installing jcapy in development mode..."
pip install -e .

# 5. Install Rich Dependency
pip install rich

# 6. Verify Installation
echo ""
echo "🧪 Verifying installation..."
which jcapy
jcapy help

echo ""
echo "✅ Setup Complete!"
echo "--------------------------------"
echo "To use jcapy, activate the venv first:"
echo "  source .venv/bin/activate"
echo ""
echo "Then run:"
echo "  jcapy help"
