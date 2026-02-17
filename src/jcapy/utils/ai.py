import os
import json
import urllib.request
import urllib.error
from jcapy.config import get_api_key

def _track_usage(provider: str, prompt: str, response: str):
    """Helper to track token usage and cost."""
    try:
        from jcapy.config import CONFIG_MANAGER

        # Estimate tokens (standard approximation: chars / 4)
        in_tokens = len(prompt) // 4
        out_tokens = len(response) // 4

        # Pricing Registry ($ per 1M tokens)
        pricing = {
            "gemini": {"in": 0.075, "out": 0.30},
            "openai": {"in": 5.00, "out": 15.00},
            "deepseek": {"in": 0.14, "out": 0.28}
        }

        rate = pricing.get(provider.lower(), {"in": 0, "out": 0})
        cost = (in_tokens * rate["in"] + out_tokens * rate["out"]) / 1_000_000

        # Update Config (Accumulated)
        current_in = CONFIG_MANAGER.get("usage.input", 0)
        current_out = CONFIG_MANAGER.get("usage.output", 0)
        current_cost = CONFIG_MANAGER.get("usage.cost", 0.0)

        CONFIG_MANAGER.set("usage.input", current_in + in_tokens)
        CONFIG_MANAGER.set("usage.output", current_out + out_tokens)
        CONFIG_MANAGER.set("usage.cost", round(current_cost + cost, 6))
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
