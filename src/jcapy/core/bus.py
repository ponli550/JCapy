from typing import Any, Callable, Dict, List, Optional
import queue
import threading
import logging

logger = logging.getLogger('jcapy.bus')


class EventBus:
    """
    A simple Pub/Sub Event Bus for JCapy (2.4).
    Decouples system components and enables async processing.
    
    Enhanced with ZMQ bridge integration for TUI ↔ Web communication.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue = queue.Queue()
        self._running = False
        self._worker_thread: threading.Thread = None
        self._zmq_publisher: Optional[Any] = None  # ZmqPublisher reference
        self._zmq_enabled = False

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Register a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Remove a callback for a specific event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def set_zmq_publisher(self, publisher: Any):
        """
        Attach a ZMQ publisher to broadcast events to Web Control Plane.
        Called during daemon/TUI initialization.
        """
        self._zmq_publisher = publisher
        self._zmq_enabled = publisher is not None
        if self._zmq_enabled:
            logger.info("EventBus: ZMQ publisher attached")

    def publish(self, event_type: str, payload: Any):
        """
        Broadcast an event to all subscribers.
        
        Also publishes to ZMQ bridge if enabled, allowing Web UI
        to receive real-time events from TUI/daemon.
        """
        # 1. Local subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"EventBus Error [Type: {event_type}]: {e}")

        # 2. ZMQ bridge (TUI → Web)
        if self._zmq_enabled and self._zmq_publisher:
            try:
                self._zmq_publisher.publish(event_type, payload)
            except Exception as e:
                logger.error(f"ZMQ publish error [Type: {event_type}]: {e}")

    def publish_local(self, event_type: str, payload: Any):
        """
        Publish only to local subscribers (skip ZMQ).
        Use for internal events that shouldn't go to Web UI.
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"EventBus Error [Type: {event_type}]: {e}")

    # Future: Background processing for high-throughput events
    # def start(self): ...
    # def stop(self): ...


# Global instance
_global_bus = EventBus()

# Alias for backward compatibility
EVENT_BUS = _global_bus

def get_event_bus() -> EventBus:
    return _global_bus


def attach_zmq_to_bus():
    """
    Attach ZMQ publisher to the global event bus.
    This enables automatic event broadcasting to Web UI.
    """
    try:
        from jcapy.core.zmq_publisher import get_zmq_bridge
        bridge = get_zmq_bridge()
        if bridge and bridge.is_running:
            _global_bus.set_zmq_publisher(bridge.publisher)
            return True
    except ImportError:
        logger.warning("ZMQ not available, bridge not attached")
    return False
