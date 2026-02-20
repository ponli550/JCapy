import subprocess
from typing import Optional, Any
from jcapy.agents.base import BaseAgent, AgentIdentity

class JCapyAgent(BaseAgent):
    """
    The default JCapy Executor Agent.
    Executes raw shell commands or high-level tasks.
    """
    def __init__(self, identity: Optional[AgentIdentity] = None, sandbox: Optional[Any] = None):
        if not identity:
            identity = AgentIdentity(
                id="agent-jcapy-executor",
                name="JCapy-Executor",
                version="1.0.0",
                permissions=["*"]
            )
        super().__init__(identity)
        from jcapy.core.sandbox import LocalSandbox
        self.sandbox = sandbox or LocalSandbox()

    def execute(self, task: str) -> str:
        """
        Executes a task by using the configured sandbox.
        """
        try:
            result = self.sandbox.run_command(task)
            return f"Output: {result}"
        except Exception as e:
            raise RuntimeError(f"Execution Error: {str(e)}")
