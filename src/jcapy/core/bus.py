from typing import Any, Callable, Dict, List
import queue
import threading

class EventBus:
    """
    A simple Pub/Sub Event Bus for JCapy (2.4).
    Decouples system components and enables async processing.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue = queue.Queue()
        self._running = False
        self._worker_thread: threading.Thread = None

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Register a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Any):
        """Broadcast an event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    # In a fully async bus, we'd queue this.
                    # For now, we execute callbacks to ensure telemetry & audit logs are immediate.
                    callback(payload)
                except Exception as e:
                    # Don't let one subscriber crash the bus
                    print(f"EventBus Error [Type: {event_type}]: {e}")

    # Future: Background processing for high-throughput events
    # def start(self): ...
    # def stop(self): ...

# Global instance
_global_bus = EventBus()

def get_event_bus() -> EventBus:
    return _global_bus
