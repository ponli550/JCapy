# SPDX-License-Identifier: Apache-2.0
import os
import json
import shutil
import sys
from jcapy.core.config_manager import ConfigManager

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(HOME, ".jcapy_config.json")
CONFIG_MANAGER = ConfigManager(CONFIG_PATH)
# Adapting BASE_DIR for the package structure, assuming resources might be near this file or handled via package data
# For now, we will assume the package root is up one level from 'config.py' (i.e. src/jcapy/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JCapy Brain Paths
JCAPY_HOME = os.path.join(HOME, ".jcapy")
EXTERNAL_LIB_PATH = os.path.join(JCAPY_HOME, "library")
# Assuming bundled library is distributed with the package, e.g., inside src/jcapy/library
BUNDLED_LIB_PATH = os.path.join(BASE_DIR, "library")
EXTERNAL_WIDGETS_PATH = os.path.join(JCAPY_HOME, "widgets")

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
    return CONFIG_MANAGER.get_all()

def save_config(data):
    CONFIG_MANAGER.set_all(data)

def get_api_key(provider):
    """Retrieves API Key with priority: 1. Environment Var, 2. Config File. Case-insensitive."""
    # Ensure .env is loaded (if available) - lazy load to avoid dependency bloat
    try:
        import dotenv
        dotenv.load_dotenv()
    except ImportError:
        pass

    provider = provider.lower()
    env_map = {
        "gemini": ["GEMINI_API_KEY", "gemini_api_key"],
        "openai": ["OPENAI_API_KEY", "openai_api_key"],
        "deepseek": ["DEEPSEEK_API_KEY", "deepseek_api_key"]
    }

    key_names = env_map.get(provider, [])
    if not key_names: return None

    # 1. Check Environment (Both cases)
    for kn in key_names:
        if os.environ.get(kn):
            return os.environ.get(kn)

    # 2. Check Config (Checking with standard uppercase key name)
    primary_key = key_names[0]
    return CONFIG_MANAGER.get(f"env.{primary_key}")

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

    CONFIG_MANAGER.set(f"env.{key_name}", key)
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
    "max_task_display": 5,  # Max tasks per column in Kanban before truncation/condensation
}

# ==========================================
# PATH CONFIGURATION
# ==========================================
def get_task_file_path():
    """Get the path to the task.md file for Kanban widget."""
    # Priority: 1. Config, 2. Project-local, 3. JCAPY_HOME
    config_path = CONFIG_MANAGER.get("paths.task_file")
    if config_path and os.path.exists(config_path):
        return config_path
    
    # Check for local task.md in current project
    local_task = os.path.join(os.getcwd(), "task.md")
    if os.path.exists(local_task):
        return local_task
    
    # Default to JCAPY_HOME
    default_path = os.path.join(JCAPY_HOME, "task.md")
    if not os.path.exists(default_path):
        # Create empty task file
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        with open(default_path, "w") as f:
            f.write("# Tasks\n\n- [ ] Example task\n")
    return default_path

def set_task_file_path(path):
    """Set the path to the task.md file."""
    CONFIG_MANAGER.set("paths.task_file", path)
    return True

def get_mcp_config_path():
    """Get the path to MCP server configuration."""
    config_path = CONFIG_MANAGER.get("paths.mcp_config")
    if config_path and os.path.exists(config_path):
        return config_path
    # Default: ~/.jcapy/mcp_servers.json
    return os.path.join(JCAPY_HOME, "mcp_servers.json")

def get_ux_preference(key: str):
    """Get a UX preference value."""
    # Use nested get: ux.key
    val = CONFIG_MANAGER.get(f"ux.{key}")
    if val is None:
        return UX_DEFAULTS.get(key)
    return val

def set_ux_preference(key: str, value):
    """Set a UX preference value."""
    CONFIG_MANAGER.set(f"ux.{key}", value)
    return True

def get_all_ux_preferences() -> dict:
    """Get all UX preferences with defaults."""
    ux = CONFIG_MANAGER.get("ux", {})
    result = UX_DEFAULTS.copy()
    result.update(ux)
    return result

# ==========================================
# DASHBOARD LAYOUT MANAGEMENT
# ==========================================
DEFAULT_LAYOUT = {
    "left_col": ["FileExplorer", "MCP"],
    "center_col": ["Kanban"],
    "right_col": ["Clock", "News", "UsageTracker"]
}

def get_dashboard_layout():
    """Get dashboard widget layout."""
    return CONFIG_MANAGER.get("dashboard_layout", DEFAULT_LAYOUT)

def set_dashboard_layout(layout):
    """Set dashboard widget layout."""
    CONFIG_MANAGER.set("dashboard_layout", layout)
    return True

def get_dashboard_dimensions():
    """Get dashboard widget dimensions (widths/heights)."""
    return CONFIG_MANAGER.get("dashboard_dimensions", {})

def set_dashboard_dimensions(dimensions):
    """Set dashboard widget dimensions (widths/heights)."""
    CONFIG_MANAGER.set("dashboard_dimensions", dimensions)
    return True
