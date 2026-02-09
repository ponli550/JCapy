"""
Error Recovery Module - Undo stack, confirmation prompts, graceful degradation.
"""
import os
import shutil
import json
import functools
from datetime import datetime, timedelta
from pathlib import Path

# Fallback ANSI colors
RED = '\033[1;31m'
YELLOW = '\033[1;33m'
GREEN = '\033[1;32m'
RESET = '\033[0m'
GREY = '\033[0;90m'
BOLD = '\033[1m'

UNDO_DIR = os.path.expanduser("~/.jcapy/undo")
UNDO_MANIFEST = os.path.join(UNDO_DIR, "manifest.json")
MAX_UNDO_ITEMS = 5
UNDO_EXPIRY_DAYS = 7


class UndoStack:
    """Manages undo history for destructive operations."""

    def __init__(self):
        self._ensure_dir()
        self._cleanup_expired()

    def _ensure_dir(self):
        """Create undo directory if it doesn't exist."""
        os.makedirs(UNDO_DIR, exist_ok=True)
        if not os.path.exists(UNDO_MANIFEST):
            self._save_manifest([])

    def _load_manifest(self) -> list:
        """Load undo manifest from disk."""
        try:
            with open(UNDO_MANIFEST, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_manifest(self, items: list):
        """Save undo manifest to disk."""
        with open(UNDO_MANIFEST, 'w') as f:
            json.dump(items, f, indent=2)

    def _cleanup_expired(self):
        """Remove undo entries older than UNDO_EXPIRY_DAYS."""
        items = self._load_manifest()
        cutoff = datetime.now() - timedelta(days=UNDO_EXPIRY_DAYS)
        valid = []

        for item in items:
            try:
                ts = datetime.fromisoformat(item['timestamp'])
                if ts >= cutoff:
                    valid.append(item)
                else:
                    # Remove backup file
                    backup_path = item.get('backup_path')
                    if backup_path and os.path.exists(backup_path):
                        if os.path.isdir(backup_path):
                            shutil.rmtree(backup_path)
                        else:
                            os.remove(backup_path)
            except (KeyError, ValueError):
                pass

        self._save_manifest(valid)

    def push(self, action_type: str, original_path: str, description: str = None) -> str:
        """
        Backup a file/directory before destructive action.
        Returns the backup path.
        """
        items = self._load_manifest()

        # Create backup
        timestamp = datetime.now().isoformat()
        safe_name = Path(original_path).name.replace(' ', '_')
        backup_name = f"{timestamp[:19].replace(':', '-')}_{safe_name}"
        backup_path = os.path.join(UNDO_DIR, backup_name)

        if os.path.isdir(original_path):
            shutil.copytree(original_path, backup_path)
        else:
            shutil.copy2(original_path, backup_path)

        # Add to manifest
        entry = {
            'action_type': action_type,
            'original_path': original_path,
            'backup_path': backup_path,
            'timestamp': timestamp,
            'description': description or f"{action_type}: {Path(original_path).name}"
        }
        items.insert(0, entry)

        # Trim to max items
        while len(items) > MAX_UNDO_ITEMS:
            old = items.pop()
            if os.path.exists(old['backup_path']):
                if os.path.isdir(old['backup_path']):
                    shutil.rmtree(old['backup_path'])
                else:
                    os.remove(old['backup_path'])

        self._save_manifest(items)
        return backup_path

    def pop(self) -> dict | None:
        """
        Undo the last action. Returns the restored item info or None.
        """
        items = self._load_manifest()
        if not items:
            return None

        entry = items.pop(0)
        backup_path = entry.get('backup_path')
        original_path = entry.get('original_path')

        if backup_path and os.path.exists(backup_path):
            # Restore to original location
            parent = Path(original_path).parent
            parent.mkdir(parents=True, exist_ok=True)

            if os.path.isdir(backup_path):
                if os.path.exists(original_path):
                    shutil.rmtree(original_path)
                shutil.copytree(backup_path, original_path)
                shutil.rmtree(backup_path)
            else:
                shutil.copy2(backup_path, original_path)
                os.remove(backup_path)

            self._save_manifest(items)
            return entry

        return None

    def list_items(self) -> list:
        """List all undo items."""
        return self._load_manifest()


def confirm(message: str, destructive: bool = False, auto_yes: bool = False) -> bool:
    """
    Display a confirmation prompt.

    - Destructive prompts show in red with [y/N] default to No
    - Non-destructive prompts show in yellow with [Y/n] default to Yes
    - auto_yes=True bypasses prompt (for --yes flag)
    """
    if auto_yes:
        return True

    if destructive:
        prompt = f"{RED}{message} [y/N]: {RESET}"
        default = False
    else:
        prompt = f"{YELLOW}{message} [Y/n]: {RESET}"
        default = True

    try:
        response = input(prompt).strip().lower()
        if not response:
            return default
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def require_dependency(name: str, fallback=None):
    """
    Decorator that checks for a dependency and falls back gracefully.

    Usage:
        @require_dependency("rich", fallback=print_plain)
        def fancy_output():
            # Uses Rich if available
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                __import__(name)
                return func(*args, **kwargs)
            except ImportError:
                if fallback:
                    return fallback(*args, **kwargs)
                else:
                    print(f"{YELLOW}⚠ Optional dependency '{name}' not installed. Using fallback.{RESET}")
                    return None
        return wrapper
    return decorator


# Singleton instance
_undo_stack = None

def get_undo_stack() -> UndoStack:
    """Get the singleton UndoStack instance."""
    global _undo_stack
    if _undo_stack is None:
        _undo_stack = UndoStack()
    return _undo_stack
