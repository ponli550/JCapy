import pytest
from jcapy.agents import AgentIdentity, BaseAgent
from jcapy.agents.security import ToolProxy

class MockAgent(BaseAgent):
    def execute(self, task: str) -> str:
        return f"Mock execute: {task}"

def sensitive_tool(data="none"):
    return f"Sensitive data: {data}"

@pytest.fixture
def agent():
    return MockAgent(AgentIdentity(id="1", name="Test", version="1"))

def test_hitl_approval_granted(agent):
    registry = {"sensitive_tool": sensitive_tool}

    # Callback that always approves
    def approve_all(tool_name, args):
        return True

    proxy = ToolProxy(
        agent,
        allowed_tools=["*"],
        tool_registry=registry,
        approval_callback=approve_all,
        approval_required_tools={"sensitive_tool"}
    )

    result = proxy.call_tool("sensitive_tool", data="approved")
    assert result == "Sensitive data: approved"

def test_hitl_approval_denied(agent):
    registry = {"sensitive_tool": sensitive_tool}

    # Callback that always denies
    def deny_all(tool_name, args):
        return False

    proxy = ToolProxy(
        agent,
        allowed_tools=["*"],
        tool_registry=registry,
        approval_callback=deny_all,
        approval_required_tools={"sensitive_tool"}
    )

    with pytest.raises(PermissionError) as excinfo:
        proxy.call_tool("sensitive_tool")
    assert "REJECTED by human operator" in str(excinfo.value)

def test_hitl_missing_callback(agent):
    registry = {"sensitive_tool": sensitive_tool}

    # Required tool but no callback provided
    proxy = ToolProxy(
        agent,
        allowed_tools=["*"],
        tool_registry=registry,
        approval_required_tools={"sensitive_tool"}
    )

    with pytest.raises(RuntimeError) as excinfo:
        proxy.call_tool("sensitive_tool")
    assert "requires approval but no approval_callback is configured" in str(excinfo.value)

def test_hitl_not_required_tool(agent):
    registry = {"normal_tool": lambda: "OK"}

    # Should not trigger approval even if a callback is present
    def approve_all(tool_name, args):
        raise RuntimeError("Should not be called")

    proxy = ToolProxy(
        agent,
        allowed_tools=["*"],
        tool_registry=registry,
        approval_callback=approve_all,
        approval_required_tools={"other_tool"}
    )

    assert proxy.call_tool("normal_tool") == "OK"
