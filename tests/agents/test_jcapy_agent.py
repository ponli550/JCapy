import pytest
from jcapy.agents.jcapy_agent import JCapyAgent
from jcapy.core.sandbox import LocalSandbox

def test_jcapy_agent_uses_sandbox():
    sandbox = LocalSandbox()
    agent = JCapyAgent(sandbox=sandbox)
    result = agent.execute("echo 'agent testing sandbox'")
    assert "Output: agent testing sandbox" in result

def test_jcapy_agent_default_sandbox():
    agent = JCapyAgent()
    assert agent.sandbox is not None
    assert isinstance(agent.sandbox, LocalSandbox)
    result = agent.execute("echo 'default'")
    assert "Output: default" in result
