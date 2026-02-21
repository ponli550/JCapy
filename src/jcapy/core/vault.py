# SPDX-License-Identifier: Apache-2.0
import os
import json
import base64
import logging
from typing import Optional, Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VAULT_PATH = os.path.expanduser("~/.jcapy/vault.json")
KEY_PATH = os.path.expanduser("~/.jcapy/.vault.key")
logger = logging.getLogger('jcapy.vault')

class JCapyVault:
    """
    Secure asset management for JCapy (Phase 7.4).
    Stores secrets in an encrypted JSON file.
    """
    def __init__(self):
        self._key = self._ensure_key()
        self._fernet = Fernet(self._key)
        self._data: Dict[str, str] = self._load()

    def _ensure_key(self) -> bytes:
        if os.path.exists(KEY_PATH):
            with open(KEY_PATH, "rb") as f:
                return f.read()

        # Generate a new key
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        return key

    def _load(self) -> Dict[str, str]:
        if not os.path.exists(VAULT_PATH):
            return {}

        try:
            with open(VAULT_PATH, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Vault load error: {e}")
            return {}

    def _save(self):
        try:
            json_data = json.dumps(self._data).encode()
            encrypted_data = self._fernet.encrypt(json_data)

            with open(VAULT_PATH, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            logger.error(f"Vault save error: {e}")

    def set(self, key: str, value: str):
        """Securely stores a secret."""
        self._data[key] = value
        self._save()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a secret from the vault."""
        return self._data.get(key, default)

    def delete(self, key: str):
        """Removes a secret from the vault."""
        if key in self._data:
            del self._data[key]
            self._save()

    def list_keys(self) -> list:
        return list(self._data.keys())

# Singleton instance
_vault_instance = None

def get_vault() -> JCapyVault:
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = JCapyVault()
    return _vault_instance

def resolve_secret(key: str, env_var: Optional[str] = None) -> Optional[str]:
    """
    Resolves a secret favoring the Vault, then environment variables.
    """
    vault = get_vault()
    val = vault.get(key)
    if val:
        return val

    if env_var:
        return os.getenv(env_var)
    return os.getenv(key)
