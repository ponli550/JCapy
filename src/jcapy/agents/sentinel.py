from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from jcapy.agents.base import BaseAgent, AgentIdentity
from jcapy.utils.ai import call_ai_agent

@dataclass
class PlanStep:
    id: int
    action: str
    description: str
    estimated_impact: str
    requires_approval: bool = False

@dataclass
class ExecutionPlan:
    goal: str
    steps: List[PlanStep]
    rationale: str

class Sentinel(BaseAgent):
    """
    Project Sentinel: The Cognitive Planner and Governor.
    Decouples 'Thinking' from 'Doing' (2.2).
    """
    def __init__(self, identity: Optional[AgentIdentity] = None):
        if not identity:
            identity = AgentIdentity(
                id="agent-sentinel",
                name="Sentinel",
                version="1.0.0",
                permissions=["*"] # The planner needs high-level visibility
            )
        super().__init__(identity)

    def generate_plan(self, goal: str, context: Optional[str] = None) -> ExecutionPlan:
        """
        Uses LLM to break down a high-level goal into discrete steps.
        """
        prompt = f"""
You are **Project Sentinel**, the planning brain of JCapy.
Break down the following goal into a step-by-step execution plan.

GOAL: {goal}
CONTEXT: {context or "No additional context provided."}

### Response Requirements:
1. Return a JSON-formatted list of steps.
2. Each step must have: id, action (one-line command/task), description, estimated_impact, and requires_approval (boolean).
3. Include a 'rationale' field explaining the overall strategy.

Example JSON output:
{{
  "steps": [
    {{ "id": 1, "action": "grep -r 'TODO' .", "description": "Locate all TODOs", "estimated_impact": "low", "requires_approval": false }}
  ],
  "rationale": "We need to find pending tasks before prioritizing them."
}}
"""
        # In a real scenario, we'd parse the JSON from call_ai_agent
        # For now, we simulate the structure
        response, err = call_ai_agent(prompt)

        # Mocking JSON parsing if error or simulation
        if err or not response:
            return self._mock_plan(goal)

        try:
            import json
            data = json.loads(response)
            steps = [PlanStep(**s) for s in data.get("steps", [])]
            return ExecutionPlan(goal=goal, steps=steps, rationale=data.get("rationale", ""))
        except:
             return self._mock_plan(goal)

    def _mock_plan(self, goal: str) -> ExecutionPlan:
        """Fallback mock for plan generation if AI fails or in dev mode."""
        return ExecutionPlan(
            goal=goal,
            rationale="Simulation mode: breaking down goal into default steps.",
            steps=[
                PlanStep(id=1, action="ls -R", description="Inventory current structure", estimated_impact="low"),
                PlanStep(id=2, action="cat README.md", description="Read project overview", estimated_impact="low")
            ]
        )

    def execute(self, task: str) -> str:
        """Sentinel plans; it doesn't execute bash directly. Delegated to JCapy."""
        return f"Sentinel [Plan Only]: {task}"
