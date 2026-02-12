import os
import shutil
import sys
import re
import time
import subprocess
from jcapy.config import (
    load_config, save_config, get_api_key,
    JCAPY_HOME, DEFAULT_LIBRARY_PATH, BASE_DIR, LOGO_PATH
)
from jcapy.ui.menu import interactive_menu
# from jcapy.ui.tui import run as run_tui # We import this inside functions to avoid circular issues or early curses init

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
BLUE = '\033[1;34m'
WHITE = '\033[1;37m'
RED = '\033[1;31m'
BOLD = '\033[1m'
RESET = '\033[0m'
GREY = '\033[0;90m'

def migrate_persona_libraries():
    """Auto-migrates persona libraries from Cellar (volatile) to ~/.jcapy (persistent)"""
    config = load_config()
    if "personas" not in config: return

    migrated = False

    for name, persona in config['personas'].items():
        if name == 'programmer': continue # handled by get_default_library_path

        old_path = persona.get('path', '')

        # Detect if the library is in the dangerous 'Cellar' or 'brew' path
        # Or if it starts with BASE_DIR which might be the cellar
        is_volatile = "Cellar/jcapy" in old_path or (BASE_DIR in old_path and JCAPY_HOME not in old_path)

        if is_volatile:
            new_path = os.path.join(JCAPY_HOME, f"library_{name}")

            # If path changed, we need to migrate
            if os.path.abspath(old_path) != os.path.abspath(new_path):
                print(f"{YELLOW}📦 Migrating persona '{name}' to persistent storage...{RESET}")

                if os.path.exists(old_path):
                    if not os.path.exists(new_path):
                        try:
                            shutil.copytree(old_path, new_path)
                            print(f"{GREEN}✔ Data moved to {new_path}{RESET}")
                        except Exception as e:
                            print(f"{RED}Failed to move data: {e}{RESET}")
                            continue # Don't update config if copy failed
                    else:
                         print(f"{GREY}Target {new_path} already exists. Updating config pointer.{RESET}")
                else:
                    print(f"{RED}⚠️  Warning: '{name}' library path was lost/missing. Pointing to new location.{RESET}")
                    if not os.path.exists(new_path):
                        os.makedirs(new_path, exist_ok=True)
                        os.makedirs(os.path.join(new_path, "skills"), exist_ok=True)

                persona['path'] = new_path
                migrated = True

    if migrated:
        save_config(config)
        print(f"{GREEN}✔ Migration complete. All personas secured in {JCAPY_HOME}{RESET}\n")

# ==========================================
# PERSONA LOGIC
# ==========================================
def load_face():
    """Loads and displays the jcapy Face (logo.md)"""
    if os.path.exists(LOGO_PATH):
        print(CYAN)
        with open(LOGO_PATH, 'r') as f:
            print(f.read())
        print(RESET)
    else:
        print(f"{CYAN}🤖 jcapy{RESET}")

def open_brain_editor():
    """Opens the entire jcapy Brain (~/.jcapy) in the preferred editor"""
    if not os.path.exists(JCAPY_HOME):
        os.makedirs(JCAPY_HOME, exist_ok=True)

    print(f"📂 Opening jcapy Brain at {JCAPY_HOME}...")

    # Determine editor
    editor = os.environ.get('EDITOR', 'open')

    if (editor == 'open' or not editor) and shutil.which('code'):
         editor = 'code'

    try:
         subprocess.call([editor, JCAPY_HOME])
    except Exception as e:
         print(f"{RED}Failed to open: {e}{RESET}")
         subprocess.call(['open', JCAPY_HOME])

def open_brain_vscode():
    # Legacy wrapper for main.py compatibility
    return open_brain_editor()

def select_persona(name=None):
    """Interactive Persona Selection & Configuration"""
    if name:
        config = load_config()
        if name in config.get("personas", {}):
            config["current_persona"] = name
            save_config(config)
            print(f"Persona switched to {name}")
            return
        else:
            print(f"Error: Persona '{name}' not found.")
            return

    load_face()

    config = load_config()
    current = config.get("current_persona", "programmer")

    print(f"{WHITE}Hi I'm jcapy, your personal assistant.{RESET}\n")
    print(f"{GREY}Current Brain: {JCAPY_HOME}{RESET}\n")

    # 1. Build Options with Status
    if "personas" not in config: config["personas"] = {}
    if "programmer" not in config["personas"]: config["personas"]["programmer"] = {"path": DEFAULT_LIBRARY_PATH}

    persona_keys = ["programmer"] + sorted([k for k in config["personas"].keys() if k != "programmer"])
    menu_options = []

    # Avoid circular import for git checks if possible, or lazy import
    from jcapy.utils.git_lib import get_git_status

    # header
    header = f"{BOLD}{'PERSONA':<20} {'STATUS':<15} {'LAST SYNC':<20}{RESET}"
    print(f"  {header}")

    for p in persona_keys:
        p_data = config["personas"].get(p, {})
        p_path = p_data.get("path", DEFAULT_LIBRARY_PATH)
        lock_status = "🔒 Locked" if p_data.get("locked") else ""

        # Get Git Status
        last_sync, pending = get_git_status(p_path)

        display_name = p.capitalize()
        if p == "programmer": display_name = "Programmer" # Shorten for table

        # Status Column
        status_col = ""
        if pending > 0:
            status_col = f"🛠️  {pending} Pending"
        elif last_sync:
            status_col = "✅ Synced"
        else:
            status_col = "Unknown"

        if lock_status:
            status_col = f"{lock_status} {status_col}"

        # Sync Column
        sync_col = last_sync if last_sync else "-"

        # Format Row
        # Name (20) | Status (15) | Sync (20)
        option_str = f"{display_name:<20} {status_col:<15} {sync_col:<20}"
        menu_options.append(option_str)

    # 2. Add Shortcuts
    menu_options.append(f"{'Manage Personas':<20}")

    # 3. Determine Default Index
    default_idx = 0
    if current in persona_keys:
        default_idx = persona_keys.index(current)

    # 4. Show Interactive Menu with Shortcuts Handler
    prompt_text = f"Who is operating right now? (Current: {current.upper()})"

    # Lazy import push to handle 'P' shortcut
    from jcapy.commands.sync import push_all_personas

    while True:
        choice_idx, char_code = interactive_menu(prompt_text, menu_options, default_index=default_idx, return_char=True)

        if char_code in ['c', 'C']:
             open_brain_vscode()
             continue # Refresh menu
        elif char_code in ['s', 'S']:
             from jcapy.commands.sync import sync_all_personas
             sync_all_personas()
             input("Press Enter to continue...")
             continue # Refresh menu
        elif char_code in ['p', 'P']:
             push_all_personas()
             input("Press Enter to continue...")
             continue # Refresh menu
        else:
             break # Selection made

    # 5. Map Choice to Persona
    manage_index = len(menu_options) - 1

    if choice_idx == manage_index:
        manage_personas_menu()
        return select_persona()

    persona_key = persona_keys[choice_idx]
    lib_path = config["personas"].get(persona_key, {}).get("path", DEFAULT_LIBRARY_PATH)

    # Ensure directory exists
    if not os.path.exists(lib_path):
        try:
            os.makedirs(os.path.join(lib_path, "skills"))
            os.makedirs(os.path.join(lib_path, "scripts"))
            print(f"{GREEN}✔ Created new memory bank for {persona_key}{RESET}")
        except:
            pass

    # Save Config
    config["current_persona"] = persona_key

    # Update personas dict
    if "personas" not in config: config["personas"] = {}
    if "programmer" not in config["personas"]: config["personas"]["programmer"] = {"path": DEFAULT_LIBRARY_PATH}
    if persona_key not in config["personas"]:
        config["personas"][persona_key] = {"path": lib_path}

    save_config(config)

    print(f"{YELLOW}User identified: {persona_key.upper()}{RESET}")

    # Transition to TUI directly
    from jcapy.ui.tui import run as run_tui
    run_tui(lib_path)

def manage_personas_menu():
    """Menu to manage (Rename, Lock, Delete) personas"""
    while True:
        options = [
            "➕ Create New Persona",
            "✏️  Rename Persona",
            "🔒 Lock/Unlock Persona",
            "🗑️  Delete Persona",
            "⬅️  Back"
        ]

        choice_idx = interactive_menu("🛠️  Persona Management", options)

        if choice_idx == 0:
            add_persona()
        elif choice_idx == 1:
            rename_persona()
        elif choice_idx == 2:
            lock_persona()
        elif choice_idx == 3:
            delete_persona()
        elif choice_idx == 4:
            break

def add_persona():
    print(f"\n{MAGENTA}➕ Create New Persona{RESET}")
    name = input(f"{CYAN}? Persona Name (give it any name): {RESET}").strip().lower()
    if not name: return

    # Normalize
    name = re.sub(r'[^a-z0-9_]', '', name)

    config = load_config()
    if "personas" not in config: config["personas"] = {}

    if name in config["personas"] or name == "programmer":
        print(f"{RED}Error: Persona '{name}' already exists.{RESET}")
        time.sleep(1)
        return

    lib_dir = f"library_{name}"
    lib_path = os.path.join(JCAPY_HOME, lib_dir)

    if not os.path.exists(lib_path):
        os.makedirs(lib_path, exist_ok=True)
        # Create subfolders
        os.makedirs(os.path.join(lib_path, "skills"), exist_ok=True)
        os.makedirs(os.path.join(lib_path, "scripts"), exist_ok=True)

    config["personas"][name] = {
        "path": lib_path,
        "created_at": str(time.time()), # Using timestamp
        "locked": False
    }

    save_config(config)
    print(f"{GREEN}✔ Persona '{name}' added at {lib_path}!{RESET}")
    time.sleep(1)

def rename_persona():
    config = load_config()
    dynamic_personas = sorted([k for k in config.get("personas", {}).keys() if k != "programmer"])

    if not dynamic_personas:
        print(f"{YELLOW}No dynamic personas to rename.{RESET}")
        time.sleep(1)
        return

    print(f"\n{YELLOW}✏️  Rename Persona{RESET}")

    options = []
    for p in dynamic_personas:
        options.append(p)
    options.append("Cancel")

    choice_idx = interactive_menu("Select Persona to rename", options)

    if choice_idx >= len(dynamic_personas):
        return

    old_name = dynamic_personas[choice_idx]

    if config["personas"][old_name].get("locked"):
        print(f"{RED}Error: Persona '{old_name}' is locked. Unlock it first.{RESET}")
        time.sleep(1)
        return

    new_name = input(f"{CYAN}? New Name for '{old_name}': {RESET}").strip().lower()
    if not new_name: return
    new_name = re.sub(r'[^a-z0-9_]', '', new_name)

    if new_name in config["personas"] or new_name == "programmer":
        print(f"{RED}Error: Name '{new_name}' already exists.{RESET}")
        time.sleep(1)
        return

    # Rename directory if it matches library_{old_name}
    old_path = config["personas"][old_name]["path"]
    new_lib_dir = f"library_{new_name}"
    new_path = os.path.join(JCAPY_HOME, new_lib_dir)

    # Standard check logic from monolithic
    standard_old_base = os.path.join(BASE_DIR, f"library_{old_name}")
    standard_old_home = os.path.join(JCAPY_HOME, f"library_{old_name}")

    if old_path == standard_old_base or old_path == standard_old_home:
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                 print(f"{RED}Error: Target path {new_path} already exists.{RESET}")
                 return

            os.rename(old_path, new_path)

        config["personas"][new_name] = config["personas"].pop(old_name)
        config["personas"][new_name]["path"] = new_path
    else:
        # Custom path? Just rename key, don't move folder
        config["personas"][new_name] = config["personas"].pop(old_name)

    save_config(config)
    print(f"{GREEN}✔ Persona renamed to '{new_name}'!{RESET}")
    time.sleep(1)

def lock_persona():
    config = load_config()
    dynamic_personas = sorted([k for k in config.get("personas", {}).keys() if k != "programmer"])

    if not dynamic_personas:
        print(f"{YELLOW}No dynamic personas to lock/unlock.{RESET}")
        time.sleep(1)
        return

    print(f"\n{CYAN}🔒 Lock/Unlock Persona{RESET}")

    options = []
    for p in dynamic_personas:
        status = "🔒 Locked" if config["personas"][p].get("locked") else "🔓 Unlocked"
        options.append(f"{p} ({status})")
    options.append("Cancel")

    choice_idx = interactive_menu("Select Persona to Lock/Unlock", options)

    if choice_idx >= len(dynamic_personas):
        return

    p_name = dynamic_personas[choice_idx]
    is_locked = config["personas"][p_name].get("locked", False)
    config["personas"][p_name]["locked"] = not is_locked

    save_config(config)
    new_status = "Locked" if not is_locked else "Unlocked"
    print(f"{GREEN}✔ Persona '{p_name}' is now {new_status}.{RESET}")
    time.sleep(1)

def delete_persona():
    config = load_config()
    dynamic_personas = sorted([k for k in config.get("personas", {}).keys() if k != "programmer"])

    if not dynamic_personas:
        print(f"{YELLOW}No dynamic personas to delete.{RESET}")
        time.sleep(1)
        return

    print(f"\n{RED}🗑️  Delete Persona{RESET}")

    options = []
    for p in dynamic_personas:
        lock_status = " 🔒" if config["personas"][p].get("locked") else ""
        options.append(f"{p}{lock_status}")
    options.append("Cancel")

    choice_idx = interactive_menu("Select Persona to DELETE", options)

    if choice_idx >= len(dynamic_personas):
        return

    p_name = dynamic_personas[choice_idx]

    if config["personas"][p_name].get("locked"):
        print(f"{RED}Error: Persona '{p_name}' is locked. Unlock it first.{RESET}")
        time.sleep(1)
        return

    print(f"\n{RED}⚠️  WARNING: You are about to delete '{p_name}'.{RESET}")
    print(f"{RED}This will PERMANENTLY delete all persona data and its library files!{RESET}")
    confirm = input(f"{YELLOW}? Type '{p_name}' to confirm deletion: {RESET}").strip()

    if confirm == p_name:
        lib_path = config["personas"][p_name]["path"]

        # Delete library directory
        if os.path.exists(lib_path):
            shutil.rmtree(lib_path)
            print(f"{YELLOW}✔ Deleted memory bank at {lib_path}{RESET}")

        # Remove from config
        del config["personas"][p_name]
        if config.get("current_persona") == p_name:
            config["current_persona"] = "programmer"

        save_config(config)
        print(f"{GREEN}✔ Persona '{p_name}' deleted successfully.{RESET}")
    else:
        print(f"{YELLOW}Deletion aborted. Confirmation name didn't match.{RESET}")

    time.sleep(1)

    time.sleep(1)

def setup_initial_persona():
    """First-time setup: Ask for user name and create admin persona."""
    print(f"\n{CYAN}Who is operating right now?{RESET}")
    name = input(f"Enter your name (e.g. 'Irfan'): ").strip()

    if not name:
        name = "User"

    safe_name = re.sub(r'[^a-z0-9_]', '', name.lower())
    if not safe_name: safe_name = "user"

    # Create library
    lib_dir = f"library_{safe_name}"
    lib_path = os.path.join(JCAPY_HOME, lib_dir)

    if not os.path.exists(lib_path):
        os.makedirs(lib_path, exist_ok=True)
        os.makedirs(os.path.join(lib_path, "skills"), exist_ok=True)
        os.makedirs(os.path.join(lib_path, "scripts"), exist_ok=True)

    config = load_config()
    if "personas" not in config: config["personas"] = {}

    config["personas"][safe_name] = {
        "path": lib_path,
        "created_at": str(time.time()),
        "locked": False
    }

    config["current_persona"] = safe_name
    config["operator_name"] = name # Save Operator Identity
    save_config(config)

    print(f"\n{GREEN}✔ Nice to meet you, {name}! Admin access granted.{RESET}")
    time.sleep(1)
    return safe_name

def ensure_operator_identity():
    """Security check for updates: Ensure we know who is operating."""
    config = load_config()

    # If we already have the operator name, we are good.
    print(f"DEBUG: Config in ensure_operator_identity: {config}")
    if "operator_name" in config:
        return config["operator_name"]

    # Security Prompt
    print(f"\n{CYAN}Who is operating right now?{RESET}")
    name = input(f"Enter your name (e.g. 'Irfan'): ").strip()

    if not name:
        name = "Operator"

    config["operator_name"] = name
    save_config(config)

    print(f"{GREEN}✔ Identity confirmed: {name}.{RESET}")
    time.sleep(0.5)
    return name

# ==========================================
# BRAINSTORMING (AI) LOGIC
# ==========================================

def check_api_keys():
    """Ensures API keys are present (Env or Config)."""
    # We only need to load config if we plan to save to it
    config = load_config()
    if 'env' not in config: config['env'] = {}

    providers = ['gemini', 'openai', 'deepseek'] # Lowercase for get_api_key
    changed = False

    print(f"\n{MAGENTA}🔑 AI Configuration {RESET}")
    for p in providers:
        key_val = get_api_key(p)
        status = f"{GREEN}Found (Env/Config){RESET}" if key_val else f"{RED}Missing{RESET}"

        # Display Status
        print(f"  • {p.capitalize()}: {status}")

        if not key_val:
            val = input(f"    {CYAN}Enter {p.capitalize()} Key (or leave blank to skip): {RESET}").strip()
            if val:
                # Save to config (Securely)
                env_key = f"{p.upper()}_API_KEY"
                config['env'][env_key] = val
                changed = True

    if changed:
        save_config(config)
        print(f"{GREEN}Keys saved securely (0o600).{RESET}")
    else:
        print(f"{GREY}Configuration checks out.{RESET}")

def get_brainstorm_prompt(context_type="skill"):
    """Returns the 2026 Fortress Standard Prompt."""
    return """
You are the **jcapy Architect Bot**. Your goal is to **refactor** the provided code into a 2026 "Fortress" Standard skill.

### Core Constraints:
1.  **Idempotency**: Ensure `mkdir`, `cd`, and `cat` operations don't fail if they've already run.
2.  **Pre-flight Checks**: Add logic to verify dependencies (e.g., `command -v kubectl`) before executing.
3.  **Observability**: Use emojis and clear `echo` statements for every major step.
4.  **Modern Patterns**: Use `[[ ]]` for shell tests and ensure all variables are quoted to handle spaces.
5.  **Harvest-Ready**: Maintain the `<!-- jcapy:EXEC -->` anchor and the Markdown structure.

### Output Format:
Return **only** the improved Markdown content. Do not include conversational filler.
"""

def brainstorm_skill(target_path, provider="local"):
    """Executes the brainstorming session."""

    # 1. Read Target Context
    if not os.path.exists(target_path):
        print(f"{RED}Error: Target {target_path} not found.{RESET}")
        return

    with open(target_path, 'r') as f:
        content = f.read()

    # 2. Prepare Prompt
    system_prompt = get_brainstorm_prompt()
    full_request = f"{system_prompt}\n\n--- TARGET CONTEXT ---\n{content}"

    # 3. Execute
    if provider == "local":
        out_file = target_path + ".prompt.txt"
        with open(out_file, 'w') as f:
            f.write(full_request)
        print(f"\n{GREEN}📝 Brainstorm Context generated:{RESET} {out_file}")
        print(f"{GREY}Copy this content into Gemini/ChatGPT/DeepSeek to get your refactor.{RESET}")

        # Auto-open
        if shutil.which('code'):
            subprocess.call(['code', out_file])
        elif sys.platform == 'darwin':
            subprocess.call(['open', out_file])

    elif provider in ["gemini", "openai", "deepseek"]:
        print(f"{YELLOW}📡 Connecting to {provider.upper()} (Simulation)...{RESET}")
        # Placeholder for actual API call
        print(f"{RED}API Integration not yet fully hydrated. Switching to Local Dump.{RESET}")
        brainstorm_skill(target_path, "local")

def run_brainstorm_wizard():
    """Interactive Wizard for jcapy Brainstorm."""
    print(f"\n{MAGENTA}🧠 jcapy Brainstorm (AI Refactor){RESET}")

    # 1. Select Target (Simple: Current Directory's files)
    files = [f for f in os.listdir('.') if f.endswith('.md') or f.endswith('.py') or f.endswith('.sh')]
    if not files:
        print(f"{RED}No suitable files found in current directory.{RESET}")
        return

    print(f"\n{CYAN}Select Target to Refactor:{RESET}")
    menu_options = files + ["Cancel"]
    choice = interactive_menu("Make a choice:", menu_options)

    if choice == len(menu_options) - 1: return
    target_file = files[choice]

    # 2. Select Provider
    print(f"\n{CYAN}Select Intelligence Engine:{RESET}")
    providers = ["Local (Generate Prompt File)", "Gemini", "OpenAI", "DeepSeek"]
    p_choice = interactive_menu("Choose Provider:", providers)

    p_map = {0: "local", 1: "gemini", 2: "openai", 3: "deepseek"}
    selected_provider = p_map[p_choice]

    # 3. Check Keys if Cloud
    if selected_provider != "local":
        # Check if key is available via Env or Config
        if not get_api_key(selected_provider):
             print(f"{YELLOW}⚠️  Key for {selected_provider} not found in Env or Config.{RESET}")
             check_api_keys() # Trigger setup
             if not get_api_key(selected_provider):
                 print(f"{RED}Aborted. No key provided.{RESET}")
                 return

    # 4. Execute
    brainstorm_skill(target_file, selected_provider)
