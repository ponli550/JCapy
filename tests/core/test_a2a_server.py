import unittest
import sys
import os
import asyncio
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from jcapy.core.a2a.server import A2AServer
from jcapy.core.a2a.protocol import SendMessageRequest, Message, Role, Part

class TestA2AServerCompliance(unittest.IsolatedAsyncioTestCase):
    async def test_server_message_handling(self):
        # Mock event bus
        bus_mock = AsyncMock()
        server = A2AServer(event_bus=bus_mock)

        # We simulate receiving a 'status update' message from an agent
        # In a2a.proto, status updates are often 'TaskStatusUpdateEvent'
        # sent via streaming, but for our simple SendMessageRequest mapping,
        # we parse the content of the Message payload.

        msg = Message(
            message_id="m-123",
            role=Role.ROLE_AGENT,
            parts=[Part(text="status: COMPLETED")]
        )
        req = SendMessageRequest(message=msg)

        # Handle the message
        await server._handle_send_message(req)

        # Verify event bus was triggered
        bus_mock.publish.assert_called_once_with("a2a_agent_message", req.message)

if __name__ == '__main__':
    unittest.main()
