import pytest
from jcapy.core.bus import EventBus

def test_bus_subscription_delivery():
    bus = EventBus()
    received = []

    def callback(payload):
        received.append(payload)

    bus.subscribe("TEST_EVENT", callback)
    bus.publish("TEST_EVENT", {"data": 123})

    assert len(received) == 1
    assert received[0]["data"] == 123

def test_bus_multiple_subscribers():
    bus = EventBus()
    received1 = []
    received2 = []

    bus.subscribe("MULTI", lambda p: received1.append(p))
    bus.subscribe("MULTI", lambda p: received2.append(p))

    bus.publish("MULTI", "hello")

    assert received1 == ["hello"]
    assert received2 == ["hello"]

def test_bus_error_isolation():
    bus = EventBus()
    received = []

    def failing_callback(p):
        raise ValueError("Boom")

    def success_callback(p):
        received.append(p)

    bus.subscribe("FAIL", failing_callback)
    bus.subscribe("FAIL", success_callback)

    # Should not crash the bus
    bus.publish("FAIL", "test")

    assert received == ["test"]
