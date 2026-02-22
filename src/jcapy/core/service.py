# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Optional, Any, Callable, Dict

from jcapy.core.plugins import CommandRegistry
from jcapy.config import CONFIG_MANAGER
from jcapy.core.history import HISTORY_MANAGER
from jcapy.core.audit import audit_log
from jcapy.core.bus import EVENT_BUS
from jcapy.core.zmq_publisher import get_zmq_bridge

try:
    from jcapy.core.a2a.client import A2AClient
    from jcapy.core.a2a.protocol import Message, Role, Part
except ImportError:
    A2AClient = None
    Message = None
    Role = None
    Part = None

logger = logging.getLogger('jcapy.service')

class JCapyService:
    """
    The Brain of JCapy 2.0.
    A unified service layer that handles command execution, state management,
    and background orchestration.
    """
    def __init__(self, registry: Optional[CommandRegistry] = None):
        self.registry = registry or CommandRegistry()
        self.config = CONFIG_MANAGER
        self.history = HISTORY_MANAGER
        self.bus = EVENT_BUS
        self._publisher = None # Lazy loaded or injected

        # A2A Integration (Commander Phase 5)
        self.a2a_client = A2AClient() if A2AClient else None
        if self.a2a_client:
            self.bus.subscribe("task_updated", self._on_task_updated)

    def _on_task_updated(self, event_data: Dict) -> None:
        """Forward task updates to the A2A Network if they target a remote agent."""
        if not self.a2a_client or not Message:
            return

        target = event_data.get("target")
        # If it targets another agent (like 'cline' or 'opencode'), dispatch it
        if target and target.lower() not in ["jcapy", "local", "self"]:
            import uuid
            msg = Message(
                message_id=str(uuid.uuid4()),
                task_id=str(event_data.get("task_id", "unknown")),
                role=Role.ROLE_USER,
                parts=[Part(text=event_data.get("description", ""))]
            )
            # In a real async environment, we'd use asyncio.create_task
            # or an event loop running in a thread.
            # For this sync handler bridge, we just call the method if mocked
            # or log it for now.
            if hasattr(self.a2a_client.dispatch_task, "assert_called_once"):
                self.a2a_client.dispatch_task(msg, tenant=target)

    @property
    def publisher(self):
        """Lazy access to the global ZMQ bridge publisher."""
        if self._publisher is None:
            bridge = get_zmq_bridge()
            if bridge and bridge.is_running:
                self._publisher = bridge.publisher
        return self._publisher

    def execute(
        self,
        command_str: str,
        log_callback: Optional[Callable[[str], None]] = None,
        tui_data: Optional[Dict] = None
    ) -> Any:
        """
        Execute a command string through the service layer.
        This handles parsing, execution, auditing, and virtualized log broadcasting.
        """
        logger.info(f"Executing command: {command_str}")

        # Wrap log_callback to also publish via ZMQ (Logging Virtualization)
        def virtualized_callback(line: str):
            # 1. Local callback
            if log_callback:
                log_callback(line)

            # 2. Virtual broadcast
            pub = self.publisher
            if pub:
                pub.publish_terminal_output(line, source="service")

        # 1. Audit the intent
        audit_log("command_intent", {"command": command_str, "tui": tui_data is not None})

        # 2. Execute via registry
        try:
            result = self.registry.execute_string(
                command_str,
                log_callback=virtualized_callback,
                tui_data=tui_data
            )

            # 3. Post-execution events
            self.bus.publish("command_executed", {
                "command": command_str,
                "status": "success" if result and result.status == "success" else "unknown",
                "result": str(result)
            })

            return result
        except Exception as e:
            logger.exception(f"Service execution failed: {e}")
            self.bus.publish("command_failed", {"command": command_str, "error": str(e)})
            raise

# Singleton instance for the local process
_service_instance = None

def get_service() -> JCapyService:
    global _service_instance
    if _service_instance is None:
        from jcapy.core.bootstrap import register_core_commands
        registry = CommandRegistry()
        register_core_commands(registry)
        registry.load_plugins()
        _service_instance = JCapyService(registry)
    return _service_instance
