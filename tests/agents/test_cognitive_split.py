import pytest
from unittest.mock import MagicMock, patch
from jcapy.agents.sentinel import Sentinel, ExecutionPlan, PlanStep
from jcapy.agents.jcapy_agent import JCapyAgent
from jcapy.core.orchestration import CognitiveOrchestrator

@pytest.fixture
def mock_planner():
    planner = Sentinel()
    planner.generate_plan = MagicMock(return_value=ExecutionPlan(
        goal="Test Goal",
        rationale="Test Rationale",
        steps=[
            PlanStep(id=1, action="echo 'step 1'", description="First step", estimated_impact="low"),
            PlanStep(id=2, action="echo 'step 2'", description="Second step", estimated_impact="low")
        ]
    ))
    return planner

@pytest.fixture
def mock_executor():
    executor = JCapyAgent()
    executor.execute = MagicMock(return_value="Success Output")
    return executor

def test_sentinel_plan_generation():
    planner = Sentinel()
    # Mock call_ai_agent to return a valid JSON plan
    with patch('jcapy.agents.sentinel.call_ai_agent') as mock_ai:
        mock_ai.return_value = ('{"steps": [{"id": 1, "action": "test", "description": "test", "estimated_impact": "low", "requires_approval": false}], "rationale": "test"}', None)
        plan = planner.generate_plan("Do something")
        assert len(plan.steps) == 1
        assert plan.steps[0].action == "test"

def test_orchestrator_run_flow(mock_planner, mock_executor):
    orchestrator = CognitiveOrchestrator(mock_planner, mock_executor)
    orchestrator.run("Test Goal")

    assert mock_planner.generate_plan.called
    assert mock_executor.execute.call_count == 2
    mock_executor.execute.assert_any_call("echo 'step 1'")
    mock_executor.execute.assert_any_call("echo 'step 2'")

def test_orchestrator_failure_stops_execution(mock_planner, mock_executor):
    # Make the first step fail
    mock_executor.execute.side_effect = Exception("Fatal Error")

    orchestrator = CognitiveOrchestrator(mock_planner, mock_executor)
    orchestrator.run("Test Goal")

    assert mock_executor.execute.call_count == 1
