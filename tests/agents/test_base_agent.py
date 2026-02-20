import pytest
from jcapy.agents import AgentIdentity, BaseAgent

class MockAgent(BaseAgent):
    def execute(self, task: str) -> str:
        return f"Executed: {task}"

def test_agent_identity_init():
    identity = AgentIdentity(
        id="test-agent",
        name="Test",
        version="1.0.0",
        permissions=["read", "write"],
        metadata={"env": "dev"}
    )
    assert identity.id == "test-agent"
    assert identity.name == "Test"
    assert identity.version == "1.0.0"
    assert "read" in identity.permissions
    assert identity.metadata["env"] == "dev"

def test_base_agent_can_execute_scope():
    identity = AgentIdentity(
        id="test-agent",
        name="Test",
        version="1.0.0",
        permissions=["fs:read"]
    )
    agent = MockAgent(identity)

    assert agent.can_execute_scope("fs:read") is True
    assert agent.can_execute_scope("fs:write") is False

def test_base_agent_wildcard_permission():
    identity = AgentIdentity(
        id="admin-agent",
        name="Admin",
        version="1.0.0",
        permissions=["*"]
    )
    agent = MockAgent(identity)

    assert agent.can_execute_scope("fs:read") is True
    assert agent.can_execute_scope("network:access") is True

def test_mock_agent_execution():
    identity = AgentIdentity(id="1", name="M", version="1")
    agent = MockAgent(identity)
    assert agent.execute("test task") == "Executed: test task"
