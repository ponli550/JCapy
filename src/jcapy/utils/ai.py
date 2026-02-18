import os
import json
import urllib.request
import urllib.error
from jcapy.config import get_api_key
from typing import Optional

def _track_usage(provider: str, prompt: str, response: str, model: Optional[str] = None):
    """Helper to track token usage and cost via UsageLogManager."""
    try:
        from jcapy.utils.usage import USAGE_LOG_MANAGER

        # Estimate tokens (standard approximation: chars / 4)
        in_tokens = len(prompt) // 4
        out_tokens = len(response) // 4

        # Use provided model or fall back to defaults
        if not model:
            if provider == "gemini": model = "gemini-1.5-flash"
            elif provider == "openai": model = "gpt-4o"
            elif provider == "deepseek": model = "deepseek-chat"
            else: model = "local"

        USAGE_LOG_MANAGER.record_hit(provider, model, in_tokens, out_tokens)
    except Exception:
        # Don't let usage tracking break the AI call
        pass

def call_ai_agent(prompt, provider='gemini'):
    """Generic helper to call LLM providers directly via urllib."""
    provider = provider.lower()
    api_key = get_api_key(provider)

    if not api_key:
        return None, f"No API key found for {provider}"

    if provider == 'gemini':
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = json.dumps({
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        try:
            with urllib.request.urlopen(req, timeout=30) as response_obj:
                result = json.loads(response_obj.read().decode('utf-8'))
                if 'candidates' in result:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    _track_usage('gemini', prompt, text)
                    return text, None
                return None, "Gemini Error: Unexpected response format"
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode('utf-8')
            return None, f"Gemini HTTP Error: {err_msg}"
        except Exception as e:
            return None, str(e)

    elif provider == 'openai' or provider == 'deepseek':
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o"
        if provider == 'deepseek':
            url = "https://api.deepseek.com/chat/completions"
            model = "deepseek-chat"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as response_obj:
                result = json.loads(response_obj.read().decode('utf-8'))
                if 'choices' in result:
                    text = result['choices'][0]['message']['content']
                    _track_usage(provider, prompt, text)
                    return text, None
                return None, f"{provider.capitalize()} Error: Unexpected response format"
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode('utf-8')
            return None, f"{provider.capitalize()} HTTP Error: {err_msg}"
        except Exception as e:
            return None, str(e)

    return None, f"Unsupported provider: {provider}"
