# Installing JCapy

JCapy is a CLI tool for solo developers following the **One-Army Protocol**. Available on macOS and Linux.

---

## macOS

### Option 1: Homebrew (Recommended)

```bash
brew tap ponli550/jcapy
brew install jcapy
```

**Upgrade:**
```bash
brew upgrade jcapy
```

### Option 2: pip

```bash
pip install jcapy
```

> Requires Python 3.11+

---

## Linux

### pip (Recommended)

```bash
pip install jcapy
```

> Requires Python 3.11+

---

## Manual Installation (Any OS)

Clone and install in development mode:

```bash
git clone https://github.com/ponli550/JCapy.git
cd JCapy/jcapy
pip install -e .
```

---

## Verify Installation

```bash
jcapy --version
jcapy help
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `command not found: jcapy` | Ensure `~/.local/bin` is in your PATH |
| Python version error | Install Python 3.11+ via `pyenv` or system package manager |
| Homebrew download fails | Run `brew update` then retry |

---

## Uninstall

**Homebrew:**
```bash
brew uninstall jcapy
```

**pip:**
```bash
pip uninstall jcapy
```
