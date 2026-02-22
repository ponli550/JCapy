from typing import Any
from .protocol import SendMessageRequest

class A2AServer:
    """
    Acts as the A2A Hub for JCapy.
    Receives compliant messages (SendMessageRequest) from remote agents
    and translates them into JCapy internal events.
    """
    def __init__(self, event_bus: Any):
        # We type hint Any instead of EventBus to avoid circular imports.
        # It expects the global EVENT_BUS object.
        self.event_bus = event_bus

    async def _handle_send_message(self, request: SendMessageRequest) -> None:
        """Process incoming A2A SendMessageRequests."""
        # For now, we simply proxy the embedded `Message` to the event bus.
        # This allows JCapy subsystems (like the CommanderHUD) to subscribe
        # to 'a2a_agent_message' and parse the `parts` logically.
        self.event_bus.publish("a2a_agent_message", request.message)
