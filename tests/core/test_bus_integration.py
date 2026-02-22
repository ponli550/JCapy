import pytest
import os
import json
import tempfile
from jcapy.core.bus import get_event_bus
from jcapy.core.audit import AuditLogger

@pytest.fixture
def temp_audit_file():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode='w+', delete=False) as tmp:
        yield tmp.name
    if os.path.exists(tmp.name):
        os.remove(tmp.name)

def test_decoupled_audit_logging(temp_audit_file):
    # Initialize AuditLogger, it will subscribe to the global bus
    logger = AuditLogger(audit_file=temp_audit_file)
    bus = get_event_bus()

    # Simulate an agent event being published to the bus
    event_payload = {
        "event_type": "TEST_DECOUPLED",
        "agent_id": "test-agent",
        "payload": {"foo": "bar"},
        "outcome": "SUCCESS"
    }

    bus.publish("AUDIT_LOG", event_payload)

    # Check if the logger captured it
    assert os.path.exists(temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "TEST_DECOUPLED"
        assert event["payload"] == {"foo": "bar"}
