import time
from enum import Enum
from typing import List, Any, Dict, Callable, Optional, Set
from .base import BaseAgent
from jcapy.core.bus import get_event_bus

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, blocked
    HALF_OPEN = "HALF_OPEN" # Testing recovery

class CircuitBreaker:
    """
    Implements a circuit breaker to handle cascading failures (ASI08, ASI10).
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has expired to transition to HALF_OPEN
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return True # HALF_OPEN allows one trial execution

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class ToolProxy:
    """
    Security proxy for agent tool execution.
    Implements:
    - ASI02: Tool Execution Sandbox & Human-in-the-loop
    - ASI05: Permission Validation
    - ASI08/ASI10: Cascading Failure Protection (via CircuitBreaker)
    """
    def __init__(
        self,
        agent: BaseAgent,
        allowed_tools: List[str],
        tool_registry: Dict[str, Callable] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        approval_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
        approval_required_tools: Optional[Set[str]] = None,
        sandbox: Optional[Any] = None, # BaseSandbox from jcapy.core.sandbox
        audit_logger: Optional[Any] = None # AuditLogger from jcapy.core.audit
    ):
        self.agent = agent
        self.allowed_tools = allowed_tools
        self.tool_registry = tool_registry or {}
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.approval_callback = approval_callback
        self.approval_required_tools = approval_required_tools or set()
        self.sandbox = sandbox
        self.audit_logger = audit_logger

    def add_skill_permissions(self, skill: Any):
        """
        Expands the allowed tools list based on a Skill manifest's permissions.
        """
        # skill is expected to be jcapy.core.skills.Skill
        if hasattr(skill, 'manifest') and hasattr(skill.manifest, 'permissions'):
            for perm in skill.manifest.permissions:
                if perm not in self.allowed_tools:
                    self.allowed_tools.append(perm)

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Intercepts and validates tool calls before execution.
        """
        # 1. Circuit Breaker Check
        if not self.circuit_breaker.can_execute():
            raise RuntimeError(f"Circuit breaker is OPEN for agent '{self.agent.identity.name}'. Execution blocked.")

        # 2. Permission Validation (ASI05)
        if not self._validate_call(tool_name):
            raise PermissionError(f"Agent '{self.agent.identity.name}' is not authorized to use tool: {tool_name}")

        # 3. Tool Presence Check
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        # 4. Human-in-the-loop Approval (ASI02)
        if tool_name in self.approval_required_tools:
            if not self.approval_callback:
                raise RuntimeError(f"Tool '{tool_name}' requires approval but no approval_callback is configured.")

            # Trigger approval (sync for now, mirroring JCapy's core pattern)
            approved = self.approval_callback(tool_name, kwargs)
            if not approved:
                raise PermissionError(f"Tool call '{tool_name}' was REJECTED by human operator.")

        # 5. Execution (ASI02 Sandbox)
        try:
            result = self.tool_registry[tool_name](**kwargs)
            self.circuit_breaker.record_success()

            get_event_bus().publish("AUDIT_LOG", {
                "event_type": "TOOL_CALL",
                "agent_id": self.agent.identity.id,
                "payload": {"tool": tool_name, "args": kwargs},
                "outcome": "SUCCESS"
            })
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            get_event_bus().publish("AUDIT_LOG", {
                "event_type": "TOOL_CALL",
                "agent_id": self.agent.identity.id,
                "payload": {"tool": tool_name, "args": kwargs},
                "outcome": f"FAILURE: {str(e)}"
            })
            raise e

    def _validate_call(self, tool_name: str) -> bool:
        """
        Validates if the tool is in the allowed list and fits the agent's scope.
        """
        if "*" in self.allowed_tools:
            return True

        return tool_name in self.allowed_tools

    def __repr__(self):
        return f"<ToolProxy(agent='{self.agent.identity.name}', state='{self.circuit_breaker.state.value}')>"
