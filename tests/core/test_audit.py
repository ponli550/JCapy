import pytest
import os
import json
import tempfile
from jcapy.core.audit import AuditLogger

@pytest.fixture
def temp_audit_file():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode='w+', delete=False) as tmp:
        yield tmp.name
    if os.path.exists(tmp.name):
        os.remove(tmp.name)

def test_audit_logger_sessions(temp_audit_file):
    logger1 = AuditLogger(audit_file=temp_audit_file)
    logger2 = AuditLogger(audit_file=temp_audit_file)

    assert logger1.session_id != logger2.session_id

def test_log_event_persistence(temp_audit_file):
    logger = AuditLogger(audit_file=temp_audit_file)

    payload = {"key": "value"}
    logger.log_event("TEST_EVENT", "agent-p", payload, outcome="SUCCESS")

    assert os.path.exists(temp_audit_file)

    with open(temp_audit_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1

        event = json.loads(lines[0])
        assert event["event_type"] == "TEST_EVENT"
        assert event["agent_id"] == "agent-p"
        assert event["payload"] == payload
        assert event["outcome"] == "SUCCESS"
        assert "timestamp" in event
        assert "session_id" in event

def test_multiple_events(temp_audit_file):
    logger = AuditLogger(audit_file=temp_audit_file)

    logger.log_event("EVENT_1", "agent-1", {"id": 1})
    logger.log_event("EVENT_2", "agent-1", {"id": 2})

    with open(temp_audit_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["event_type"] == "EVENT_1"
        assert json.loads(lines[1])["event_type"] == "EVENT_2"
