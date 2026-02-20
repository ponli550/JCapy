import pytest
import time
from jcapy.agents import AgentIdentity, BaseAgent
from jcapy.agents.security import ToolProxy, CircuitBreaker, CircuitState

class MockAgent(BaseAgent):
    def execute(self, task: str) -> str:
        return f"Mock execute: {task}"

def failing_tool():
    raise RuntimeError("Tool failed!")

def success_tool():
    return "Success"

@pytest.fixture
def agent():
    return MockAgent(AgentIdentity(id="1", name="Test", version="1"))

def test_circuit_breaker_trips(agent):
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    proxy = ToolProxy(agent, allowed_tools=["*"], tool_registry={"fail": failing_tool}, circuit_breaker=cb)

    # First failure
    with pytest.raises(RuntimeError):
        proxy.call_tool("fail")
    assert cb.state == CircuitState.CLOSED

    # Second failure - should trip
    with pytest.raises(RuntimeError):
        proxy.call_tool("fail")
    assert cb.state == CircuitState.OPEN

    # Third call - should be blocked by proxy
    with pytest.raises(RuntimeError) as excinfo:
        proxy.call_tool("fail")
    assert "Circuit breaker is OPEN" in str(excinfo.value)

def test_circuit_breaker_recovery(agent):
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
    proxy = ToolProxy(agent, allowed_tools=["*"], tool_registry={"fail": failing_tool, "pass": success_tool}, circuit_breaker=cb)

    # Trip it
    with pytest.raises(RuntimeError):
        proxy.call_tool("fail")
    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    time.sleep(0.15)

    # Should be HALF_OPEN on next call check
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success in HALF_OPEN should CLOSE it
    assert proxy.call_tool("pass") == "Success"
    assert cb.state == CircuitState.CLOSED

def test_circuit_breaker_half_open_failure(agent):
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
    proxy = ToolProxy(agent, allowed_tools=["*"], tool_registry={"fail": failing_tool}, circuit_breaker=cb)

    # Trip it
    with pytest.raises(RuntimeError):
        proxy.call_tool("fail")

    # Wait for timeout
    time.sleep(0.15)

    # Failure in HALF_OPEN should immediately RE-OPEN
    with pytest.raises(RuntimeError):
        proxy.call_tool("fail")
    assert cb.state == CircuitState.OPEN
