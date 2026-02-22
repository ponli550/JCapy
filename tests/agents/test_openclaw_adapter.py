import pytest
from jcapy.agents import AgentIdentity
from jcapy.agents.openclaw_adapter import OpenClawAdapter

class MockExternalAgent:
    def run_task(self, task, tools):
        if "secret_tool" in task:
            return tools["secret_tool"]()
        return f"Processed: {task}"

def test_openclaw_adapter_execution():
    identity = AgentIdentity(id="ext-1", name="External", version="1")
    ext_agent = MockExternalAgent()
    adapter = OpenClawAdapter(identity, ext_agent, allowed_tools=[], tool_registry={})

    assert adapter.execute("hello") == "Processed: hello"

def test_openclaw_adapter_sandboxed_tool_success():
    identity = AgentIdentity(id="ext-1", name="External", version="1")
    ext_agent = MockExternalAgent()

    def my_tool():
        return "Tool Success"

    registry = {"secret_tool": my_tool}
    adapter = OpenClawAdapter(
        identity,
        ext_agent,
        allowed_tools=["secret_tool"],
        tool_registry=registry
    )

    assert adapter.execute("use secret_tool") == "Tool Success"

def test_openclaw_adapter_sandboxed_tool_blocked():
    identity = AgentIdentity(id="ext-1", name="External", version="1")
    ext_agent = MockExternalAgent()

    # Tool is in registry but NOT allowed for this adapter
    registry = {"secret_tool": lambda: "Forbidden"}
    adapter = OpenClawAdapter(
        identity,
        ext_agent,
        allowed_tools=["other_tool"],
        tool_registry=registry
    )

    # The external agent tries to use 'secret_tool' which it doesn't even see in its tool dict
    # or if it tries to call it via the proxy manually, it should fail.
    result = adapter.execute("use secret_tool")
    assert "External Agent Error" in result
    assert "secret_tool" in result

def test_openclaw_adapter_missing_interface():
    identity = AgentIdentity(id="ext-1", name="External", version="1")
    adapter = OpenClawAdapter(identity, object(), allowed_tools=[], tool_registry={})

    result = adapter.execute("any task")
    assert "External Agent Error" in result
    assert "does not implement" in result
