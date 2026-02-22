from .protocol import SendMessageRequest, Message

class A2AClient:
    def __init__(self, hub_url: str = "http://localhost:8080"):
        self.hub_url = hub_url

    async def _send_message(self, request: SendMessageRequest) -> bool:
        # Placeholder for actual network transport (HTTP POST or gRPC)
        # Expected to send `request.model_dump_json()` across the wire
        return True

    async def dispatch_task(self, message: Message, tenant: str = None) -> bool:
        """
        Dispatch a compliant A2A Message to the remote agent.
        Wraps the Message inside a SendMessageRequest.
        """
        request = SendMessageRequest(
            tenant=tenant,
            message=message
        )
        return await self._send_message(request)
