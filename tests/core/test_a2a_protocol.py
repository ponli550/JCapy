import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from jcapy.core.a2a.protocol import (
    Role, TaskState, Part, Message, TaskStatus, Task, SendMessageRequest
)

class TestOfficialA2AProtocol(unittest.TestCase):
    def test_role_enum(self):
        self.assertEqual(Role.ROLE_USER.value, 1)
        self.assertEqual(Role.ROLE_AGENT.value, 2)

    def test_part_serialization(self):
        text_part = Part(text="Hello world")
        self.assertEqual(text_part.text, "Hello world")

        # Test validation: exactly one content type should be set in real usage,
        # though Pydantic lets us be flexible if we use Optional.
        # It maps to the `oneof content` in protobuf.

    def test_message_serialization(self):
        msg = Message(
            message_id="msg-1",
            role=Role.ROLE_USER,
            parts=[Part(text="Fix the login screen")]
        )
        self.assertEqual(msg.message_id, "msg-1")
        self.assertEqual(msg.role, Role.ROLE_USER)
        self.assertEqual(len(msg.parts), 1)
        self.assertEqual(msg.parts[0].text, "Fix the login screen")

    def test_task_serialization(self):
        status = TaskStatus(state=TaskState.TASK_STATE_SUBMITTED)
        task = Task(id="t-1", context_id="ctx-1", status=status)

        self.assertEqual(task.id, "t-1")
        self.assertEqual(task.status.state, TaskState.TASK_STATE_SUBMITTED)

    def test_send_message_request(self):
        msg = Message(
            message_id="m-1",
            role=Role.ROLE_AGENT,
            parts=[Part(text="Done.")]
        )
        req = SendMessageRequest(message=msg)
        self.assertEqual(req.message.message_id, "m-1")

if __name__ == '__main__':
    unittest.main()
