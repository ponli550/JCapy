import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from jcapy.core.service import JCapyService
from jcapy.core.a2a.protocol import Message, Role

class TestA2AServiceIntegrationCompliance(unittest.TestCase):
    def test_a2a_bus_integration_compliant(self):
        service = JCapyService(registry=MagicMock())
        self.assertIsNotNone(service.a2a_client)

        service.a2a_client.dispatch_task = MagicMock(return_value=True)

        # Simulating a local task update that should trigger an A2A broadcast
        service.bus.publish("task_updated", {
            "task_id": "test-123",
            "description": "Cross-agent test",
            "target": "cline"
        })

        # Assert dispatch task called once
        service.a2a_client.dispatch_task.assert_called_once()

        # Verify it was called with a compliant Message object
        call_args = service.a2a_client.dispatch_task.call_args[0]
        dispatched_msg = call_args[0]

        self.assertIsInstance(dispatched_msg, Message)
        self.assertEqual(dispatched_msg.role, Role.ROLE_USER)
        self.assertEqual(dispatched_msg.task_id, "test-123")
        self.assertEqual(len(dispatched_msg.parts), 1)
        self.assertEqual(dispatched_msg.parts[0].text, "Cross-agent test")

if __name__ == '__main__':
    unittest.main()
