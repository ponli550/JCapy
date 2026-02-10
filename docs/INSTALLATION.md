# JCapy Installation Guide

## Quick Install

### Option 1: Homebrew (macOS - Recommended)
```bash
brew tap ponli550/jcapy
brew install jcapy
jcapy help
```

### Option 2: pip/pipx
```bash
pipx install jcapy
# or
pip install jcapy
jcapy help
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'jcapy'"

**Cause:** Multiple jcapy installations conflict. A dev `.venv` version may be overriding the system install.

**Fix:**
```bash
# Check which jcapy is being used
which jcapy

# If it shows .venv path, deactivate or use absolute path:
deactivate  # if in venv
hash -r     # refresh shell PATH cache

# Or use Homebrew version directly:
/opt/homebrew/bin/jcapy help
```

### Removing Conflicting Installations
```bash
# Remove pipx version
pipx uninstall jcapy

# Remove pip version
pip uninstall jcapy

# Remove .venv (if in dev directory)
rm -rf .venv/bin/jcapy

# Verify only Homebrew remains
which -a jcapy
# Should show: /opt/homebrew/bin/jcapy
```

---

## For Developers

### Running Dev Version (without publishing)
```bash
cd /path/to/jcapy
python -m venv .venv
source .venv/bin/activate
pip install -e .
jcapy help
```

### Switching Between Dev ↔ Production
```bash
# Use production (Homebrew)
deactivate
hash -r
jcapy help

# Use dev version
source .venv/bin/activate
jcapy help
```
