# SPDX-License-Identifier: Apache-2.0
import os
import json
import shutil
import sys

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(HOME, ".jcapy_config.json")
# Adapting BASE_DIR for the package structure, assuming resources might be near this file or handled via package data
# For now, we will assume the package root is up one level from 'config.py' (i.e. src/jcapy/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JCapy Brain Paths
JCAPY_HOME = os.path.join(HOME, ".jcapy")
EXTERNAL_LIB_PATH = os.path.join(JCAPY_HOME, "library")
# Assuming bundled library is distributed with the package, e.g., inside src/jcapy/library
BUNDLED_LIB_PATH = os.path.join(BASE_DIR, "library")

def get_default_library_path():
    # 1. Env Var
    if os.environ.get("JCAPY_LIBRARY_PATH"):
        return os.environ.get("JCAPY_LIBRARY_PATH")

    # 2. External Home (~/.jcapy/library) - FORCE PERSISTENCE
    if not os.path.exists(EXTERNAL_LIB_PATH):
        if os.path.exists(BUNDLED_LIB_PATH):
             try:
                 print(f"📦 First Run: Migrating bundled library to {EXTERNAL_LIB_PATH}...")
                 shutil.copytree(BUNDLED_LIB_PATH, EXTERNAL_LIB_PATH)
             except Exception as e:
                 print(f"⚠️  Migration Warning: Could not copy bundled library: {e}")
        else:
             # Create empty if bundle missing
             os.makedirs(EXTERNAL_LIB_PATH, exist_ok=True)

    # 3. Always return the external path as the source of truth
    return EXTERNAL_LIB_PATH

DEFAULT_LIBRARY_PATH = get_default_library_path()
TEMPLATE_PATH = os.path.join(DEFAULT_LIBRARY_PATH, "templates/skill.md")
# We'll need to ensure logo.md is moved or embedded. For now, referencing it relative to BASE_DIR if it exists there.
LOGO_PATH = os.path.join(BASE_DIR, "logo.md")

# ==========================================
# CONFIGURATION MANAGEMENT
# ==========================================
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
             return {}
    return {}

def save_config(data):
    # Secure Save: Ensure file is read/write by owner only (0o600)
    try:
        # Prepare file descriptor with atomic exclusive creation if possible, or truncation
        fd = os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        # Force permissions for existing files
        os.chmod(CONFIG_PATH, 0o600)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_api_key(provider):
    """Retrieves API Key with priority: 1. Environment Var, 2. Config File"""
    provider = provider.lower()
    env_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }

    key_name = env_map.get(provider)
    if not key_name: return None

    # 1. Check Environment
    if os.environ.get(key_name):
        return os.environ.get(key_name)

    # 2. Check Config
    config = load_config()
    return config.get('env', {}).get(key_name)

def set_api_key(provider, key):
    """Securely saves an API key to the config file."""
    provider = provider.lower()
    env_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }

    key_name = env_map.get(provider)
    if not key_name:
        return False, f"Unsupported provider: {provider}"

    config = load_config()
    if 'env' not in config:
        config['env'] = {}

    config['env'][key_name] = key
    save_config(config)
    return True, f"Successfully saved {provider.capitalize()} API key."

def get_active_library_path():
    config = load_config()
    current_persona = config.get("current_persona", "programmer")
    personas = config.get("personas", {})

    if current_persona in personas:
        return personas[current_persona].get("path", DEFAULT_LIBRARY_PATH)

    # Default to Programmer/Default path
    return DEFAULT_LIBRARY_PATH

def get_current_persona_name():
    config = load_config()
    return config.get("current_persona", "programmer").capitalize()

def load_config_local():
    """Load local .jcapyrc project config"""
    config_path = os.path.join(os.getcwd(), ".jcapyrc")
    if os.path.exists(config_path):
        try:
             with open(config_path, 'r') as f:
                 import json
                 return json.load(f)
        except:
             return {}
    return {}

# ==========================================
# UX PREFERENCE MANAGEMENT
# ==========================================
UX_DEFAULTS = {
    "theme": "default",
    "hints": True,
    "reduced_motion": False,
    "accessible": False,
    "audio_mode": "muted",  # Options: muted, beeps, voice, custom
}

def get_ux_preference(key: str):
    """Get a UX preference value."""
    config = load_config()
    ux = config.get("ux", {})
    return ux.get(key, UX_DEFAULTS.get(key))

def set_ux_preference(key: str, value):
    """Set a UX preference value."""
    config = load_config()
    if "ux" not in config:
        config["ux"] = {}
    config["ux"][key] = value
    save_config(config)
    return True

def get_all_ux_preferences() -> dict:
    """Get all UX preferences with defaults."""
    config = load_config()
    ux = config.get("ux", {})
    result = UX_DEFAULTS.copy()
    result.update(ux)
    return result
