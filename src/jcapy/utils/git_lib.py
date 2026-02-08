import subprocess
import os
from typing import Optional, Tuple

def get_git_remote_url(path: str) -> Optional[str]:
    """
    Retrieves the Git remote URL for the given path.
    Returns None if the path is not a git repository or if there is no remote.
    """
    if not os.path.exists(os.path.join(path, ".git")):
        return None

    try:
        result = subprocess.run(
            ["git", "-C", path, "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        # git command not found
        return None

def get_git_status(path: str) -> Tuple[Optional[str], int]:
    """Returns (last_sync_time, pending_count) tuple"""
    if not os.path.exists(os.path.join(path, ".git")):
        return None, 0

    try:
        # Get uncommitted changes count
        pending_out = subprocess.check_output(f"git -C {path} status --porcelain | wc -l", shell=True).decode().strip()
        pending = int(pending_out) if pending_out else 0

        # Get last commit relative time
        last_sync = subprocess.check_output(f"git -C {path} log -1 --format='%cr'", shell=True).decode().strip()

        return last_sync, pending
    except Exception:
        return None, 0
