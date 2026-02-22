from typing import List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from jcapy.agents.sentinel import Sentinel, ExecutionPlan
from jcapy.agents.base import BaseAgent
from jcapy.core.bus import get_event_bus

console = Console()

class CognitiveOrchestrator:
    """
    Coordinates the 'Cognitive Split' (2.2).
    Handoff flow: User Goal -> Sentinel (Plan) -> User (Approval) -> BaseAgent (Action).
    """
    def __init__(self, planner: Sentinel, executor: BaseAgent, audit_logger: Optional[Any] = None):
        self.planner = planner
        self.executor = executor
        self.audit_logger = audit_logger

    def run(self, goal: str, context: Optional[str] = None):
        """
        Executes the cognitive orchestration loop.
        """
        # 1. Generate Plan
        console.print(f"\n[bold magenta]📂 Sentinel is drafting an execution plan...[/bold magenta]")
        plan = self.planner.generate_plan(goal, context)

        get_event_bus().publish("AUDIT_LOG", {
            "event_type": "PLAN_GENERATED",
            "agent_id": self.planner.identity.id,
            "payload": {"goal": goal, "rationale": plan.rationale, "steps_count": len(plan.steps)}
        })

        # 2. Display Plan
        self._display_plan(plan)

        # 3. Execution Loop
        console.print(f"\n[bold green]🚀 Commencing targeted execution...[/bold green]")
        for step in plan.steps:
            console.print(f"\n[bold cyan]Step {step.id}: {step.action}[/bold cyan]")
            console.print(f"[dim]{step.description}[/dim]")

            # Here we would integrate with the ToolProxy/HITL if step.requires_approval

            try:
                result = self.executor.execute(step.action)
                console.print(f"[green]✔ Success:[/green] {result}")

                get_event_bus().publish("AUDIT_LOG", {
                    "event_type": "STEP_RESULT",
                    "agent_id": self.executor.identity.id,
                    "payload": {"step_id": step.id, "action": step.action},
                    "outcome": "SUCCESS"
                })
            except Exception as e:
                console.print(f"[bold red]❌ Step {step.id} Failed:[/bold red] {e}")

                get_event_bus().publish("AUDIT_LOG", {
                    "event_type": "STEP_RESULT",
                    "agent_id": self.executor.identity.id,
                    "payload": {"step_id": step.id, "action": step.action},
                    "outcome": f"FAILURE: {str(e)}"
                })
                # Future logic: Call Sentinel to re-plan
                break

        console.print(f"\n[bold green]✅ Orchestration Complete.[/bold green]")

    def _display_plan(self, plan: ExecutionPlan):
        table = Table(title=f"Execution Plan: {plan.goal}", show_header=True, header_style="bold blue")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Action", style="cyan")
        table.add_column("Impact", style="yellow")
        table.add_column("Approval", style="magenta")

        for step in plan.steps:
            approval_req = "Yes" if step.requires_approval else "No"
            table.add_row(str(step.id), step.action, step.estimated_impact, approval_req)

        console.print(Panel(plan.rationale, title="Sentinel Rationale", border_style="magenta"))
        console.print(table)
