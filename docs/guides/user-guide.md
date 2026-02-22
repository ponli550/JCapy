# JCapy User Guide

## Getting Started

### Installation

```bash
# Via Homebrew (macOS)
brew install ponli550/jcapy/jcapy

# Via pip
pip install jcapy

# From source
git clone https://github.com/ponli550/jcapy.git
cd jcapy
pip install -e .
```

### First Run

```bash
# Start the TUI
jcapy

# Run a quick command
jcapy --help

# Self-diagnostic
jcapy doctor
```

## TUI Navigation

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `z` | Toggle Zen Mode |
| `e` | Edit Layout |
| `c` | Collapse Column |
| `:` | Open command bar |
| `?` | Show help |
| `d` | Debug mode (dev) |

### Main Screens

1. **Dashboard**: Overview of projects, tasks, and status
2. **Brainstorm**: AI-assisted brainstorming sessions
3. **Budget**: Token usage and cost tracking
4. **Harvest**: Knowledge extraction and organization
5. **Management**: Project and configuration management

## Commands

### Core Commands

```bash
jcapy brain "your request"    # AI-powered task execution
jcapy config set key value    # Set configuration
jcapy config get key          # Get configuration value
jcapy doctor                  # Run diagnostics
jcapy skills list             # List available skills
jcapy skills install <name>   # Install a skill
```

### Project Management

```bash
jcapy project init            # Initialize a new project
jcapy project status          # Show project status
jcapy project sync            # Sync with remote
```

## Skills

Skills are plugins that extend JCapy's capabilities.

### Installing Skills

```bash
# List available skills
jcapy skills list

# Install a skill
jcapy skills install security-audit

# Use a skill
jcapy brain --skill security-audit "audit this codebase"
```

### Available Skills

| Skill | Description |
|-------|-------------|
| `hello-world` | Test skill installation |
| `systematic-debugging` | Structured debugging methodology |
| `code-review-checklist` | Code review guidelines |
| `architectural-design` | Architecture patterns |
| `scale-infrastructure` | Infrastructure scaling |
| `security-audit` | Security assessment |
| `aws` | AWS best practices |
| `kanban` | Task management |
| `mcp-creator` | MCP server creation |

## Configuration

Configuration is stored in `~/.jcapy/config.json`

### Key Settings

```json
{
  "theme": "default",
  "ai_provider": "anthropic",
  "model": "claude-3-opus",
  "sandbox": "docker",
  "audit_enabled": true
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `JCAPY_SANDBOX` | Sandbox type (local/docker) |
| `JCAPY_QUIET` | Suppress non-essential output |

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -e . --force-reinstall
   ```

2. **Docker sandbox not working**
   ```bash
   docker pull python:3.11-slim
   ```

3. **Permission denied errors**
   - Check your `jcapy.yaml` skill manifests for required permissions

### Getting Help

```bash
jcapy help
jcapy help <command>
```

## Tips & Best Practices

1. **Use Zen Mode** for focused work (`z` key)
2. **Run `jcapy doctor`** after updates
3. **Check audit logs** in `~/.jcapy/audit/` for debugging
4. **Use skills** for specialized tasks instead of manual prompting