from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class AgentIdentity:
    """
    Represents the unique identity of a JCapy Agent.
    Following ASI03 (Agent Identity & Base) security principles.
    """
    id: str
    name: str
    version: str
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """
    Abstract Base Class for all JCapy Agents.
    Provides standard identity and capability checking.
    """
    def __init__(self, identity: AgentIdentity):
        self.identity = identity

    @abstractmethod
    def execute(self, task: str) -> str:
        """
        Execute a given task.
        """
        pass

    def can_execute_scope(self, scope: str) -> bool:
        """
        Check if the agent has permission to execute within a specific scope.
        """
        # Simple string-based permission check for now
        # "*" allows everything
        if "*" in self.identity.permissions:
            return True
        return scope in self.identity.permissions

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.identity.name}', version='{self.identity.version}')>"
