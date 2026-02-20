import os
import json
import time
import uuid
from typing import Any, Dict, Optional

class AuditLogger:
    """
    Persistent, append-only logger for JCapy Agent events (2.4).
    Logs to ~/.jcapy/audit.jsonl
    """
    def __init__(self, audit_file: Optional[str] = None):
        if audit_file is None:
            home = os.path.expanduser("~")
            self.audit_file = os.path.join(home, ".jcapy", "audit.jsonl")
        else:
            self.audit_file = audit_file

        os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)
        self.session_id = str(uuid.uuid4())

        # Subscribe to AUDIT_LOG events (2.4 Decoupling)
        from jcapy.core.bus import get_event_bus
        get_event_bus().subscribe("AUDIT_LOG", self.handle_event)

    def handle_event(self, event_data: Dict[str, Any]) -> None:
        """
        Callback for EventBus to handle audit-related events.
        """
        self.log_event(
            event_type=event_data.get("event_type", "UNKNOWN"),
            agent_id=event_data.get("agent_id", "system"),
            payload=event_data.get("payload", {}),
            outcome=event_data.get("outcome")
        )

    def log_event(
        self,
        event_type: str,
        agent_id: str,
        payload: Dict[str, Any],
        outcome: Optional[str] = None
    ) -> None:
        """
        Append an event to the audit log.
        """
        event = {
            "timestamp": time.time(),
            "session_id": self.session_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "payload": payload,
            "outcome": outcome
        }

        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
        except IOError as e:
            # We don't want to crash the agent if logging fails,
            # but we should at least print to stderr in dev
            pass

# Global instance for easy access
_global_audit_logger = AuditLogger()

def get_audit_logger() -> AuditLogger:
    return _global_audit_logger
