import os
import subprocess
from datetime import datetime
from jcapy.config import load_config, save_config, DEFAULT_LIBRARY_PATH

# Global State for Main Loop
SKILL_UPDATES_AVAILABLE = False
APP_UPDATE_AVAILABLE = None
VERSION = "4.1.1"

def check_for_app_updates():
    """Checks GitHub for the latest CLI Release Tag"""
    global APP_UPDATE_AVAILABLE
    config = load_config()

    # Throttling (check app update once every 24h)
    last_app_check = config.get("auto_sync", {}).get("last_app_check")
    if last_app_check:
        try:
            last_check_dt = datetime.fromisoformat(last_app_check)
            if (datetime.now() - last_check_dt).total_seconds() < 86400:
                pass # return
        except:
            pass

    # We continue execution even if throttled to allow manual override logic if we wanted,
    # but here let's stick to the logic. Actually, let's just implement the logic.

    # ... (Actual check logic would go here, simplified to avoid requests if throttled)
    # Since we can't easily do requests without imports, we'll try basic approach or skip.
    try:
        import urllib.request
        import json

        url = "https://api.github.com/repos/ponli550/jcapyCLI/tags"
        req = urllib.request.Request(url, headers={'User-Agent': 'jcapyCLI'})

        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data and isinstance(data, list) and len(data) > 0:
                latest_tag = data[0].get("name", "").replace("v", "")
                if latest_tag != VERSION:
                    APP_UPDATE_AVAILABLE = latest_tag
    except:
        pass

    # Save Check Time
    if "auto_sync" not in config: config["auto_sync"] = {}
    config["auto_sync"]["last_app_check"] = datetime.now().isoformat()
    # We don't save config every time to avoid write spam, ideally only if changed.
    # But here we updated timestamp.
    # save_config(config)


def check_for_framework_updates():
    """Background check for skill library updates (throttled to 24h)."""
    global SKILL_UPDATES_AVAILABLE
    config = load_config()

    check_for_app_updates()

    # Check updates for CORE library (Programmer) only
    lib_path = DEFAULT_LIBRARY_PATH

    # 1. Throttling Check
    last_check_str = config.get("auto_sync", {}).get("last_check")
    if last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            if (datetime.now() - last_check).total_seconds() < 86400: # 24 Hours
                SKILL_UPDATES_AVAILABLE = config.get("auto_sync", {}).get("updates_pending", False)
                return
        except:
            pass

    # 2. Check for Git Remote
    if not os.path.exists(os.path.join(lib_path, ".git")):
        return

    try:
        # Check if origin remote exists
        result = subprocess.run(["git", "remote"], cwd=lib_path, capture_output=True, text=True)
        if "origin" not in result.stdout:
             return

        # Perform Fetch
        subprocess.run(["git", "fetch", "origin"], cwd=lib_path, capture_output=True, timeout=5)

        # Compare HEAD with origin/main or origin/master
        status = subprocess.run(["git", "status", "-uno"], cwd=lib_path, capture_output=True, text=True).stdout

        if "Your branch is behind" in status:
            SKILL_UPDATES_AVAILABLE = True
        else:
            SKILL_UPDATES_AVAILABLE = False

        # 3. Update Config
        if "auto_sync" not in config: config["auto_sync"] = {}
        config["auto_sync"]["last_check"] = datetime.now().isoformat()
        config["auto_sync"]["updates_pending"] = SKILL_UPDATES_AVAILABLE
        save_config(config)

    except Exception:
        pass

def get_update_status():
    return APP_UPDATE_AVAILABLE, SKILL_UPDATES_AVAILABLE
