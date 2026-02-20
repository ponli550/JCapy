from typing import Any, Dict, List, Optional, Callable
from .base import BaseAgent, AgentIdentity
from .security import ToolProxy, CircuitBreaker

class ExternalAgentProtocol:
    """
    Protocol definition for what we expect from an external agent.
    """
    def run_task(self, task: str, tools: Dict[str, Callable]) -> str:
        raise NotImplementedError

class OpenClawAdapter(BaseAgent):
    """
    Adapter for third-party agents following the OpenClaw pattern (ASI04).
    Sandboxes all tool access through ToolProxy.
    """
    def __init__(
        self,
        identity: AgentIdentity,
        external_agent: Any,
        allowed_tools: List[str],
        tool_registry: Dict[str, Callable]
    ):
        super().__init__(identity)
        self.external_agent = external_agent
        # Strict sandbox: Third-party agents always get a dedicated ToolProxy
        self.proxy = ToolProxy(
            agent=self,
            allowed_tools=allowed_tools,
            tool_registry=tool_registry,
            circuit_breaker=CircuitBreaker(failure_threshold=2) # Stricter for external code
        )

    def execute(self, task: str) -> str:
        """
        Executes a task by bridging to the external agent.
        The external agent is given access ONLY to the ToolProxy's call_tool method.
        """
        # We wrap the proxy's call_tool to simplify the interface for the external agent
        sandboxed_tools = {
            name: lambda n=name, **kwargs: self.proxy.call_tool(n, **kwargs)
            for name in self.proxy.allowed_tools if name != "*"
        }

        try:
            # Bridging to the external agent's primary entry point
            # We assume the external agent has a method like 'run' or 'run_task'
            if hasattr(self.external_agent, "run_task"):
                return self.external_agent.run_task(task, sandboxed_tools)
            elif hasattr(self.external_agent, "run"):
                return self.external_agent.run(task, sandboxed_tools)
            else:
                raise AttributeError("External agent does not implement 'run_task' or 'run' methods.")
        except Exception as e:
            # Any failure in the external agent is caught here
            return f"External Agent Error: {str(e)}"

    def __repr__(self):
        return f"<OpenClawAdapter(name='{self.identity.name}', external_type='{type(self.external_agent).__name__}')>"
