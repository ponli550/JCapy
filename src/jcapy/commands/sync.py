import os
import shutil
import time
import subprocess
from datetime import datetime
from jcapy.config import load_config, save_config, DEFAULT_LIBRARY_PATH
from jcapy.utils.git_lib import get_git_status
from jcapy.ui.menu import interactive_menu

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
RED = '\033[1;31m'
RESET = '\033[0m'
GREY = '\033[0;90m'

def sync_all_personas():
    """Smart Sync: Pulls updates or Clones missing brains. Interactive & Robust."""
    config = load_config()
    personas = config.get("personas", {})
    if "programmer" not in personas: personas["programmer"] = {"path": DEFAULT_LIBRARY_PATH}

    # 1. Build Menu Options
    persona_keys = ["programmer"] + sorted([k for k in personas.keys() if k != "programmer"])
    menu_options = ["Sync All (Default)"]

    for p in persona_keys:
        p_data = personas.get(p, {})
        path = p_data.get("path")
        remote = p_data.get("remote_url", "No Remote")
        short_remote = remote.replace("https://", "").replace("git@", "")[:25] + "..." if len(remote) > 25 else remote

        last_sync, pending = get_git_status(path)
        status_icon = "✅" if pending == 0 else "⚠️ Dirty"

        menu_options.append(f"{p.capitalize()} [{short_remote}] {status_icon}")

    # 2. Select Target
    print(f"\n{MAGENTA}🔄 jcapy Sync Protocol{RESET}")
    choice_idx = interactive_menu("Select Target to Sync:", menu_options)

    targets = []
    if choice_idx == 0:
        targets = persona_keys # All
    else:
        targets = [persona_keys[choice_idx - 1]] # Specific

    print(f"\n{MAGENTA}⬇️  Syncing Selected Brains...{RESET}")
    config_changed = False

    for name in targets:
        p_data = personas.get(name, {})
        path = p_data.get("path")
        remote_url = p_data.get("remote_url")

        print(f"  {CYAN}• {name.capitalize()}:{RESET} ", end="", flush=True)

        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".git")):
                # Check for dirty state
                _, pending = get_git_status(path)

                # Logic: Stash -> Pull (Rebase) -> Pop
                commands = []
                if pending > 0:
                    print(f"{YELLOW} Local changes ({pending}). Stashing...{RESET}", end="")
                    commands.append(["git", "stash"])

                commands.append(["git", "pull", "--rebase"])

                if pending > 0:
                    commands.append(["git", "stash", "pop"])

                # Execute
                success = True
                for cmd in commands:
                    res = subprocess.run(cmd, cwd=path, capture_output=True, text=True)
                    if res.returncode != 0:
                        # Fallback: If pull failed, maybe upstream isn't set?
                        if "pull" in cmd and "no tracking information" in res.stderr:
                             try:
                                 current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path).decode().strip()
                             except:
                                 current_branch = "main"

                             print(f"{YELLOW} Setting upstream to origin/{current_branch}...{RESET}")
                             subprocess.run(["git", "branch", "--set-upstream-to", f"origin/{current_branch}", current_branch], cwd=path, capture_output=True)
                             # Retry pull
                             res = subprocess.run(cmd, cwd=path, capture_output=True, text=True)

                        if res.returncode != 0:
                            print(f"\n    {RED}❌ Error during '{cmd[1]}':{RESET} {res.stderr.strip()}")
                            success = False
                            break

                if success:
                    print(f"{GREEN}Updated ✔{RESET}")

            else:
                 # Exists but not Git-linked
                 print(f"{YELLOW}Exists but not Git-linked.{RESET}")
                 if input(f"    {CYAN}? Initialize and link to remote? (y/N): {RESET}").strip().lower() == 'y':
                     new_remote = input(f"    {CYAN}? Remote Git URL: {RESET}").strip()
                     if new_remote:
                         try:
                             subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
                             subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=True, capture_output=True)
                             subprocess.run(["git", "remote", "add", "origin", new_remote], cwd=path, check=True, capture_output=True)
                             p_data["remote_url"] = new_remote
                             config_changed = True
                             print(f"    {GREY}Linking...{RESET}")
                             subprocess.run(["git", "pull", "origin", "main"], cwd=path, capture_output=True)
                             print(f"    {GREEN}Linked & Synced ✔{RESET}")
                         except Exception as e:
                             print(f"    {RED}Failed: {e}{RESET}")

        elif remote_url:
            # Clone Recovery
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                res = subprocess.run(["git", "clone", remote_url, path], capture_output=True, text=True)
                if res.returncode == 0:
                    print(f"{GREEN}Recovered (Clone) ☁️ -> 💾{RESET}")
                else:
                    print(f"{RED}Clone Failed: {res.stderr}{RESET}")
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
        else:
             # Missing & No Remote
             print(f"{RED}Missing & No Remote.{RESET}")
             if input(f"    {CYAN}? Clone from a URL? (y/N): {RESET}").strip().lower() == 'y':
                 new_remote = input(f"    {CYAN}? Remote Git URL: {RESET}").strip()
                 if new_remote:
                     try:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        res = subprocess.run(["git", "clone", new_remote, path], capture_output=True, text=True)
                        if res.returncode == 0:
                            print(f"    {GREEN}Recovered (Clone) ☁️ -> 💾{RESET}")
                            p_data["remote_url"] = new_remote
                            config_changed = True
                        else:
                            print(f"    {RED}Clone Failed.{RESET}")
                     except Exception as e:
                        print(f"    {RED}Error: {e}{RESET}")

    if config_changed:
        save_config(config)

    print(f"\n{GREEN}Sync Complete.{RESET}")
    time.sleep(2)


def push_all_personas():
    """Iterates through all personas and pushes changes. Interactive."""
    config = load_config()
    personas = config.get("personas", {})
    if "programmer" not in personas: personas["programmer"] = {"path": DEFAULT_LIBRARY_PATH}

    # 1. Build Menu Options
    persona_keys = ["programmer"] + sorted([k for k in personas.keys() if k != "programmer"])
    menu_options = ["Push All (Default)"]

    for p in persona_keys:
        p_data = personas.get(p, {})
        path = p_data.get("path")
        remote = p_data.get("remote_url", "No Remote")
        short_remote = remote.replace("https://", "").replace("git@", "")[:20] + "..." if len(remote) > 20 else remote

        last_sync, pending = get_git_status(path)
        status = f"[{pending} pending]" if pending > 0 else "Clean"

        menu_options.append(f"{p.capitalize()} [{short_remote}] {status}")

    # 2. Select Target
    print(f"\n{MAGENTA}🚀 jcapy Push Protocol{RESET}")
    choice_idx = interactive_menu("Select Target to Push:", menu_options)

    if choice_idx == 0:
        targets = persona_keys # All
    else:
        targets = [persona_keys[choice_idx - 1]] # Specific

    print(f"\n{MAGENTA}⬆️  Pushing Selected Brains...{RESET}")
    config_changed = False

    for name in targets:
        p_data = personas.get(name, {})
        path = p_data.get("path")

        if not path or not os.path.exists(path): continue

        print(f"  {CYAN}• {name.capitalize()}:{RESET} ", end="", flush=True)

        # Check for Git
        if not os.path.exists(os.path.join(path, ".git")):
             print(f"{YELLOW} Not a git repo.{RESET}")
             if input(f"    {CYAN}? Initialize Git? (y/N): {RESET}").strip().lower() == 'y':
                 try:
                     subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
                     subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=True, capture_output=True)
                     print(f"    {GREEN}Initialized.{RESET}")
                 except:
                     print(f"    {RED}Failed.{RESET}")
                     continue
             else:
                 continue

        # Check Remote
        has_remote = False
        try:
            res = subprocess.run(["git", "remote"], cwd=path, capture_output=True, text=True)
            if "origin" in res.stdout:
                has_remote = True
        except: pass

        if not has_remote:
            print(f"{YELLOW} No remote configured.{RESET}")
            if input(f"    {CYAN}? Add Remote URL? (y/N): {RESET}").strip().lower() == 'y':
                url = input(f"    {CYAN}? URL: {RESET}").strip()
                if url:
                    try:
                        subprocess.run(["git", "remote", "add", "origin", url], cwd=path, check=True, capture_output=True)
                        print(f"    {GREEN}Remote added.{RESET}")
                        personas[name]["remote_url"] = url
                        config_changed = True
                        has_remote = True
                    except:
                        print(f"    {RED}Failed to add remote.{RESET}")

        if has_remote:
            try:
                # Add
                subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
                # Commit (ignore empty)
                subprocess.run(["git", "commit", "-m", f"Brain Sync: {datetime.now()}"], cwd=path, capture_output=True)

                # Pull (Rebase) - Sync with remote before pushing
                print(f"    {GREY}Syncing (Rebase)...{RESET}", end="", flush=True)
                pull_res = subprocess.run(["git", "pull", "origin", "main", "--rebase"], cwd=path, capture_output=True, text=True)

                if pull_res.returncode != 0:
                     # Check if it was just "no upstream"
                     if "no tracking information" in pull_res.stderr:
                         pass # New repo, just push
                     else:
                         print(f"\n    {YELLOW}Pull/Rebase encountered issues. Trying to push anyway (might fail)...{RESET}")

                # Push
                res = subprocess.run(["git", "push", "origin", "main"], cwd=path, capture_output=True, text=True)
                if res.returncode != 0:
                     # Try master fallback
                     res = subprocess.run(["git", "push", "origin", "master"], cwd=path, capture_output=True, text=True)

                if res.returncode == 0:
                    print(f"{GREEN}Synced ✔{RESET}")
                    # Update config if remote wasn't there
                    if "remote_url" not in personas[name]:
                        # Get URL
                        url = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=path).decode().strip()
                        personas[name]["remote_url"] = url
                        config_changed = True
                else:
                    print(f"{RED}Push Failed.{RESET}")
                    # Prompt to Change Remote?
                    if input(f"    {CYAN}? Push Failed. Change Remote URL? (y/N): {RESET}").strip().lower() == 'y':
                        new_url = input(f"    {CYAN}? New URL: {RESET}").strip()
                        if new_url:
                            subprocess.run(["git", "remote", "set-url", "origin", new_url], cwd=path, check=True)
                            personas[name]["remote_url"] = new_url
                            config_changed = True
                            print(f"    {GREEN}Remote Updated. Try pushing again.{RESET}")

            except Exception as e:
                 print(f"{RED}Error: {e}{RESET}")
        else:
             print(f"{GREY} Skipped (No Remote){RESET}")

    if config_changed:
        save_config(config)

    print(f"\n{GREEN}Done.{RESET}")
    time.sleep(2)
