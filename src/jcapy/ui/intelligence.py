import re
import threading
import time
from collections import deque

class Alert:
    def __init__(self, tier, message, suggestion, action_cmd=None):
        self.tier = tier # 1 (System), 2 (App)
        self.message = message
        self.suggestion = suggestion
        self.action_cmd = action_cmd
        self.timestamp = time.time()

class RuleEngine:
    """Detects patterns in log lines and suggests actions."""

    # Tier 1: Infrastructure (High Confidence)
    SYSTEM_RULES = [
        (r"CrashLoopBackOff", "Pod is crashing repeatedly", "Inspect with 'describe pod'", "describe pod"),
        (r"OOMKilled", "Container killed due to Out of Memory", "Check resource limits", "describe pod"),
        (r"Error: ImagePullBackOff", "Failed to pull image", "Verify image path and credentials", "describe pod"),
        (r"Connection refused", "Service endpoint unreachable", "Check service/port mapping", "doctor")
    ]

    # Tier 2: Application (Subtle Suggestions)
    APP_RULES = [
        (r"ModuleNotFoundError: No module named '([^']+)'", "Missing Python dependency", "Apply pip-sync?", "apply pip-sync"),
        (r"ImportError: cannot import name '([^']+)'", "Python Import conflict", "Check for circular imports?", "doctor"),
        (r"UnhandledPromiseRejectionWarning", "Node.js Unhandled Promise", "Inspect stack trace for missing awaits", "logs --limit 50"),
        (r"django.db.utils.ProgrammingError: column [^ ]+ does not exist", "Missing DB migrations", "Apply migrations?", "apply db-migrate"),
        (r"panic: ", "Go Runtime Panic", "Severe application crash detected", "logs --limit 100")
    ]

    def match(self, line):
        alerts = []
        # Check Tier 1
        for pattern, msg, sugg, cmd in self.SYSTEM_RULES:
            if re.search(pattern, line):
                alerts.append(Alert(1, msg, sugg, cmd))

        # Check Tier 2
        for pattern, msg, sugg, cmd in self.APP_RULES:
            match = re.search(pattern, line)
            if match:
                # Interpolate if needed (e.g. module name)
                final_sugg = sugg
                if "([^']+)" in pattern:
                    final_sugg = f"Apply pip-sync for '{match.group(1)}'?"
                alerts.append(Alert(2, msg, final_sugg, cmd))

        return alerts

class AutonomousObserver(threading.Thread):
    """Background thread that monitors the ProcessManager output buffer."""

    def __init__(self, proc_manager):
        super().__init__(daemon=True)
        self.proc = proc_manager
        self.engine = RuleEngine()
        self.last_index = 0
        self.active_alerts = deque(maxlen=20) # Keep recent alerts
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        while self.running:
            try:
                # Work with a snapshot of the buffer
                with self.proc.lock:
                    current_output = list(self.proc.full_output)

                if len(current_output) > self.last_index:
                    new_lines = current_output[self.last_index:]
                    for line in new_lines:
                        found_alerts = self.engine.match(line)
                        if found_alerts:
                            with self.lock:
                                self.active_alerts.extend(found_alerts)

                    self.last_index = len(current_output)

                time.sleep(0.5) # Scan interval
            except Exception:
                time.sleep(1) # Backoff on error

    def get_latest_alerts(self, tier=None):
        with self.lock:
            if tier:
                return [a for a in self.active_alerts if a.tier == tier]
            return list(self.active_alerts)

    def clear_alerts(self):
        with self.lock:
            self.active_alerts.clear()

    def stop(self):
        self.running = False
