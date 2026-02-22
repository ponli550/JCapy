# AI Provider Setup Guide

JCapy integrates with multiple AI providers for enhanced features like brainstorming, code analysis, and intelligent suggestions. This guide explains how to configure each provider.

## Quick Setup

Set your API key via environment variable or JCapy config:

```bash
# Option 1: Environment Variable (Recommended)
export GEMINI_API_KEY="your-api-key-here"

# Option 2: JCapy Config
jcapy config set env.GEMINI_API_KEY "your-api-key-here"
```

## Supported Providers

### 1. Google Gemini (Recommended)

**Get your API key:** [Google AI Studio](https://aistudio.google.com/app/apikey)

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

**Features:**
- Fast responses
- Generous free tier
- Good for code analysis and brainstorming

### 2. OpenAI

**Get your API key:** [OpenAI Platform](https://platform.openai.com/api-keys)

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**Features:**
- GPT-4 and GPT-3.5 models
- Excellent code understanding
- Works with `brainstorm` command

### 3. DeepSeek

**Get your API key:** [DeepSeek Platform](https://platform.deepseek.com/)

```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

**Features:**
- Cost-effective alternative
- Strong coding capabilities
- Good for longer contexts

## Priority Order

JCapy tries providers in this order:
1. **Gemini** (default, fastest)
2. **OpenAI** (fallback)
3. **DeepSeek** (fallback)

## Usage in JCapy

### Brainstorm Command

```bash
# Brainstorm with AI
jcapy brainstorm myfile.py --provider gemini

# Or let JCapy auto-select
jcapy brainstorm myfile.py
```

### AI Agent Widget

The AI Agent widget in the dashboard shows real-time AI thoughts when configured. It uses the first available provider.

### MCP Tools

The `brainstorm` MCP tool is available for AI-powered code refactoring:

```python
# Via MCP client
result = brainstorm(file_content, "Refactor into a JCapy skill")
```

## Security Best Practices

### DO:
- Use environment variables for API keys
- Add `.env` to `.gitignore`
- Rotate keys periodically

### DON'T:
- Commit API keys to version control
- Share keys in chat/logs
- Use keys in public repositories

## Troubleshooting

### "No AI keys configured"

Set at least one API key:
```bash
export GEMINI_API_KEY="your-key"
```

### "Brainstorming failed"

1. Check your API key is valid
2. Verify network connectivity
3. Check API quota/limits

### Rate Limits

If you hit rate limits:
1. Wait a few minutes
2. Try a different provider
3. Reduce request frequency

## Cost Management

JCapy tracks AI usage in the Usage Tracker widget. Set a budget limit:

```bash
jcapy config set usage.session_limit 5.0  # $5.00 per session
```

The widget will warn you when approaching the limit.

## Advanced: Custom Provider

To add a custom AI provider, extend the `call_ai_agent` function in `jcapy/utils/ai.py`:

```python
def call_ai_agent(prompt: str, provider: str = "gemini") -> tuple:
    if provider == "custom":
        # Your custom implementation
        return response, None
    # ... existing providers
```

---

*Last updated: February 2026*
*JCapy v4.1+*