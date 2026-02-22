import pytest
from jcapy.agents import AgentIdentity, BaseAgent
from jcapy.agents.security import ToolProxy

class MockAgent(BaseAgent):
    def execute(self, task: str) -> str:
        return f"Mock execute: {task}"

def mock_tool_fn(param="default"):
    return f"Tool result with {param}"

@pytest.fixture
def secure_proxy():
    identity = AgentIdentity(id="1", name="SecurityAgent", version="1.0.0", permissions=["fs:read"])
    agent = MockAgent(identity)
    registry = {"read_file": mock_tool_fn, "write_file": mock_tool_fn}
    return ToolProxy(agent, allowed_tools=["read_file"], tool_registry=registry)

def test_tool_proxy_allows_authorized_tool(secure_proxy):
    result = secure_proxy.call_tool("read_file", param="test")
    assert result == "Tool result with test"

def test_tool_proxy_blocks_unauthorized_tool(secure_proxy):
    with pytest.raises(PermissionError) as excinfo:
        secure_proxy.call_tool("write_file")
    assert "not authorized to use tool: write_file" in str(excinfo.value)

def test_tool_proxy_wildcard_allowed():
    identity = AgentIdentity(id="1", name="Admin", version="1.0.0")
    agent = MockAgent(identity)
    registry = {"any_tool": mock_tool_fn}
    proxy = ToolProxy(agent, allowed_tools=["*"], tool_registry=registry)

    assert proxy.call_tool("any_tool") == "Tool result with default"

def test_tool_proxy_missing_tool(secure_proxy):
    # 'read_file' is authorized in the fixture but we can remove it from registry for this test
    del secure_proxy.tool_registry["read_file"]
    with pytest.raises(ValueError) as excinfo:
        secure_proxy.call_tool("read_file")
    assert "not found in registry" in str(excinfo.value)
