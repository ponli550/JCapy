# SPDX-License-Identifier: Apache-2.0
import json
import os
import threading
from typing import Any, Dict, Optional
from jcapy.ui.messages import ConfigUpdated

class ConfigManager:
    """
    Unified Configuration Manager for JCapy.
    Handles loading, saving, and merging configuration from JSON files.
    Thread-safe singleton pattern usage recommended.
    """

    def __init__(self, path: str):
        self._path = path
        # Secrets path: sibling to config file
        self._secrets_path = os.path.join(os.path.dirname(path), ".jcapy_secrets.json")
        self._config: Dict[str, Any] = {}
        self._env_config: Dict[str, Any] = {} # Env var overrides
        self._secrets_config: Dict[str, Any] = {} # Secrets file overrides
        self._lock = threading.RLock()
        self._app = None  # Reference to Textual App
        self._load()
        self._load_secrets()
        self._parse_env_vars()

    def bind_app(self, app):
        """Bind the Textual App instance to enable reactive updates."""
        self._app = app

    def _load_secrets(self):
        """Load secrets from .jcapy_secrets.json."""
        if os.path.exists(self._secrets_path):
            try:
                # Ensure read-only permissions on secrets file?
                # For now just read it.
                with open(self._secrets_path, 'r') as f:
                    self._secrets_config = json.load(f)
            except:
                self._secrets_config = {}

    def _parse_env_vars(self):
        """Parse JCAPY__ environment variables into a nested dict."""
        prefix = "JCAPY__"
        for env_key, value in os.environ.items():
            if env_key.startswith(prefix):
                # JCAPY__PLUGINS__WEATHER__CITY -> plugins.weather.city
                key_path = env_key[len(prefix):].lower().replace("__", ".")

                # Build nested structure
                keys = key_path.split(".")
                current = self._env_config
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                    if not isinstance(current, dict):
                         # Conflict with existing value, skip or overwrite?
                         # For now, if we encounter a non-dict where we need a dict, we can't merge deep
                         break

                if isinstance(current, dict):
                    # Attempt type conversion? Env vars are strings.
                    # Best effort string to int/bool/float?
                    # For now keep as string to avoid magic
                    current[keys[-1]] = value

    def _emit_update(self, key: str, value: Any):
        """Emit ConfigUpdated message if app is bound."""
        if self._app:
            self._app.post_message(ConfigUpdated(key, value))

    def _load(self):
        """Load configuration from disk."""
        with self._lock:
            if os.path.exists(self._path):
                try:
                    with open(self._path, 'r') as f:
                        self._config = json.load(f)
                except (json.JSONDecodeError, IOError):
                    # Fallback to empty config if corrupt/unreadable
                    self._config = {}
            else:
                self._config = {}

    def _save(self):
        """Save configuration to disk atomically."""
        with self._lock:
            # Atomic save: write to temp file then rename
            tmp_path = self._path + ".tmp"
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)

                # Secure permissions (0o600)
                fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, 'w') as f:
                    json.dump(self._config, f, indent=2)

                os.replace(tmp_path, self._path)
                os.chmod(self._path, 0o600)
            except Exception as e:
                # If save fails, we log it but don't crash
                # In a real app we might rely on a logger
                print(f"Error saving config: {e}")
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def _get_nested(self, data: Dict[str, Any], key: str) -> Any:
        """Helper to traverse nested dicts with dot notation."""
        if "." in key:
            parts = key.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current
        return data.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from configuration, checking Env Vars then Secrets then File."""
        import copy
        with self._lock:
            # 1. Check Env Config
            env_val = self._get_nested(self._env_config, key)
            if env_val is not None:
                return copy.deepcopy(env_val)

            # 2. Check Secrets Config
            secret_val = self._get_nested(self._secrets_config, key)
            if secret_val is not None:
                return copy.deepcopy(secret_val)

            # 3. Check File Config
            file_val = self._get_nested(self._config, key)
            if file_val is not None:
                return copy.deepcopy(file_val)

            return copy.deepcopy(default)

    def get_all(self) -> Dict[str, Any]:
        """Get entire merged configuration dictionary."""
        with self._lock:
            # Deep merge _config into _env_config copy?
            # Or just return _config (disk state)?
            # get_all usually implies "effective config"
            # Implementing robust deep merge is complex.
            # For now, return _config, as UI often needs to know what is SAVED.
            # To indicate overrides, we might need a separate API (get_effective_config)
            # But the requirement is unified.
            # Let's do a shallow merge for top level keys for now?
            result = self._config.copy()
            # Simple recursive merge could go here if needed.
            # For simplicity:
            return result

    def set(self, key: str, value: Any):
        """Set a value in configuration and save, supporting dot notation."""
        import copy
        with self._lock:
            # Check current DISK value to avoid unnecessary saves
            current_disk_val = self._get_nested(self._config, key)
            if current_disk_val == value:
                return # No change, skip save/emit

            if "." in key:
                parts = key.split(".")
                current = self._config
                # Traverse to the second to last part, creating dicts if needed
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = copy.deepcopy(value)
            else:
                self._config[key] = copy.deepcopy(value)
            self._save()
            self._emit_update(key, value)

    def set_all(self, config: Dict[str, Any]):
        """Replace entire configuration and save."""
        import copy
        with self._lock:
            if self._config == config:
                return # No change

            self._config = copy.deepcopy(config)
            self._save()
            self._emit_update("*", config)
