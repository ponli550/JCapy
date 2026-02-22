# SPDX-License-Identifier: Apache-2.0
import os
import json
import uuid
import time
from typing import Dict, Any, Optional
from jcapy.config import load_config, get_all_ux_preferences
import dotenv
try:
    dotenv.load_dotenv()
except (ImportError, OSError):
    pass
from posthog import Posthog

# Ideally use posthog-python, but we might not want to force dependency immediately
# We can use a simple HTTP request or check if installed
try:
    import posthog
    HAS_POSTHOG = True
except ImportError:
    HAS_POSTHOG = False

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY") # Public key or read from env. DONT COMMIT REAL KEY.
POSTHOG_HOST = os.getenv("POSTHOG_HOST") # Public key or read from env. DONT COMMIT REAL KEY.
# For Open Source, usually we use a proxy or just don't track by default unless opt-in
# OR we use a public project key that only accepts ingestion.
# Since user said "Privacy First: Add a flag in jcapy config to let users opt-out."
# and "For a startup, you need to know Retention".

class TelemetryClient:
    def __init__(self):
        self.config = load_config()
        self.prefs = get_all_ux_preferences()
        self.enabled = str(self.prefs.get("telemetry", "true")).lower() == "true"
        self.user_id = self._get_or_create_user_id()
        self.shadow_log_path = os.path.expanduser("~/.jcapy/shadow_log.jsonl")

        if self.enabled and HAS_POSTHOG:
            posthog = Posthog(api_key=POSTHOG_API_KEY, host=POSTHOG_HOST)
            pass

    def _get_or_create_user_id(self) -> str:
        # Check config for UUID, else generate and save
        uid = self.config.get("telemetry_id")
        if not uid:
            uid = str(uuid.uuid4())
            # Save back to config would be ideal but load_config returns dict/object
            # We skip saving for now to avoid side effects in this simple implementation
        return uid

    def track(self, event: str, properties: Dict[str, Any] = None):
        if not self.enabled:
            return

        if properties is None:
            properties = {}

        # Enrich
        properties["version"] = "4.0.0" # Should import VERSION
        properties["platform"] = os.uname().sysname

        # Log to file for "Shadow Mode" / Debug if not sending
        # or actually send if PostHog configured
        if event == "shadow_mode_interaction":
            self._log_to_local_file(event, properties)

        # For now, just a placeholder or debug print if verbose
        # print(f"[Telemetry] {event}: {properties}")

    def _log_to_local_file(self, event: str, properties: Dict[str, Any]):
        """Append event to local JSONL file for transparency."""
        entry = {
            "timestamp": time.time(),
            "event": event,
            "properties": properties,
            "user_id": self.user_id
        }
        try:
            with open(self.shadow_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # telemetry should never crash app
            pass

    def capture_shadow_mode(self, context: str, suggestion: str, user_action: str):
        """
        Record 'Golden Fix' candidates.
        Suggestion: What JCapy thought was the fix.
        User Action: What the user actually executed.
        """
        self.track("shadow_mode_interaction", {
            "context": context,
            "suggestion": suggestion,
            "user_action": user_action,
            "match": suggestion == user_action
        })

_client = TelemetryClient()

def get_telemetry() -> TelemetryClient:
    return _client
