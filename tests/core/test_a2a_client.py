import unittest
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from jcapy.core.a2a.client import A2AClient
from jcapy.core.a2a.protocol import Message, Part, Role

class TestA2AClientCompliance(unittest.IsolatedAsyncioTestCase):
    async def test_a2a_client_dispatch(self):
        client = A2AClient(hub_url="mock://localhost")

        # Test creating a compliant message payload
        msg = Message(
            message_id="cli-123",
            role=Role.ROLE_USER,
            parts=[Part(text="Fix the bug")]
        )

        # Mock transport for test
        sent_payloads = []
        async def mock_send(request_obj):
            sent_payloads.append(request_obj)
            return True

        client._send_message = mock_send

        # Dispatch a compliant Message directly
        result = await client.dispatch_task(msg)
        self.assertTrue(result)

        self.assertEqual(len(sent_payloads), 1)
        sent_req = sent_payloads[0]

        # Verify the client wraps it in a SendMessageRequest
        self.assertEqual(sent_req.message.message_id, "cli-123")
        self.assertEqual(sent_req.message.parts[0].text, "Fix the bug")

if __name__ == '__main__':
    unittest.main()
