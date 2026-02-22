# SPDX-License-Identifier: Apache-2.0
"""
JCapy ZMQ Publisher Module

Provides ZeroMQ-based communication between TUI and Web Control Plane.
- ZmqPublisher: PUB socket for broadcasting events (port 5555)
- ZmqRpcServer: REP socket for handling commands (port 5556)
"""

import os
import json
import threading
import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger('jcapy.zmq')

# Try to import zmq, provide graceful fallback
try:
    import zmq
    import zmq.asyncio
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logger.warning("pyzmq not installed. TUI ↔ Web communication disabled.")


class ZmqPublisher:
    """
    ZeroMQ PUB socket for broadcasting events to Web Control Plane.
    
    Usage:
        publisher = ZmqPublisher()
        publisher.start()
        publisher.publish("TERMINAL_OUTPUT", {"line": "Hello World"})
    """
    
    def __init__(self, port: int = 5555, bind_addr: str = "tcp://*"):
        self._enabled = ZMQ_AVAILABLE
        self.port = port
        self.bind_addr = bind_addr
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._started = False
        
    def start(self) -> bool:
        """Initialize and bind the PUB socket."""
        if not self._enabled:
            logger.warning("ZMQ not available, publisher not started")
            return False
            
        if self._started:
            return True
            
        try:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.PUB)
            self._socket.set_hwm(1000)  # High water mark for message buffering
            self._socket.bind(f"{self.bind_addr}:{self.port}")
            self._started = True
            logger.info(f"ZMQ Publisher bound to {self.bind_addr}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start ZMQ Publisher: {e}")
            self._started = False
            return False
    
    def stop(self):
        """Close the PUB socket."""
        if self._socket:
            self._socket.close()
            self._socket = None
        if self._context:
            self._context.term()
            self._context = None
        self._started = False
        logger.info("ZMQ Publisher stopped")
    
    def publish(self, topic: str, data: Any) -> bool:
        """
        Publish an event to all subscribers.
        
        Args:
            topic: Event topic (e.g., "TERMINAL_OUTPUT", "COMMAND_EXECUTED")
            data: Event payload (will be JSON serialized)
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._enabled or not self._started:
            return False
            
        try:
            # Multi-part message: [topic, payload]
            topic_bytes = topic.encode('utf-8')
            
            if isinstance(data, str):
                payload_bytes = data.encode('utf-8')
            else:
                payload_bytes = json.dumps(data, default=str).encode('utf-8')
                
            self._socket.send_multipart([topic_bytes, payload_bytes], zmq.NOBLOCK)
            logger.debug(f"Published: {topic}")
            return True
        except zmq.Again:
            # Socket buffer full, drop message
            logger.warning(f"ZMQ buffer full, dropping message: {topic}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish {topic}: {e}")
            return False
    
    def publish_heartbeat(self, status: Dict[str, Any]) -> bool:
        """Publish a heartbeat event for daemon health monitoring."""
        return self.publish("HEARTBEAT", {
            "timestamp": datetime.now().isoformat(),
            "status": status
        })
    
    def publish_terminal_output(self, line: str, source: str = "tui") -> bool:
        """Publish a terminal output line."""
        return self.publish("TERMINAL_OUTPUT", {
            "line": line,
            "source": source,
            "timestamp": datetime.now().isoformat()
        })
    
    def publish_command(self, command: str, result: Optional[Dict] = None) -> bool:
        """Publish a command execution event."""
        return self.publish("COMMAND_EXECUTED", {
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def publish_mode_change(self, mode: str, persona: Optional[str] = None) -> bool:
        """Publish a mode/persona change event."""
        return self.publish("MODE_CHANGED", {
            "mode": mode,
            "persona": persona,
            "timestamp": datetime.now().isoformat()
        })
    
    def publish_audit(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Publish an audit log event."""
        return self.publish("AUDIT_LOG", {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        })
    
    def __repr__(self):
        status = "running" if self._started else "stopped"
        return f"<ZmqPublisher port={self.port} status={status}>"


class ZmqRpcServer:
    """
    ZeroMQ REP socket for handling commands from Web Control Plane.
    
    Usage:
        server = ZmqRpcServer(command_handler=my_handler)
        server.start()  # Runs in background thread
    """
    
    def __init__(
        self, 
        port: int = 5556, 
        bind_addr: str = "tcp://*",
        command_handler: Optional[Callable[[str, Dict], Dict]] = None
    ):
        self._enabled = ZMQ_AVAILABLE
        self.port = port
        self.bind_addr = bind_addr
        self.command_handler = command_handler
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
    def set_command_handler(self, handler: Callable[[str, Dict], Dict]):
        """Set the command handler function."""
        self.command_handler = handler
    
    def start(self) -> bool:
        """Start the RPC server in a background thread."""
        if not self._enabled:
            logger.warning("ZMQ not available, RPC server not started")
            return False
            
        if self._running:
            return True
            
        try:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REP)
            self._socket.bind(f"{self.bind_addr}:{self.port}")
            self._running = True
            
            # Start listener thread
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            
            logger.info(f"ZMQ RPC Server bound to {self.bind_addr}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start ZMQ RPC Server: {e}")
            self._running = False
            return False
    
    def stop(self):
        """Stop the RPC server."""
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
        if self._context:
            self._context.term()
            self._context = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("ZMQ RPC Server stopped")
    
    def _listen_loop(self):
        """Main listen loop for handling RPC requests."""
        if not self._socket:
            return
            
        while self._running:
            try:
                # Wait for next request with timeout
                if self._socket.poll(1000):  # 1 second timeout
                    message = self._socket.recv_string()
                    
                    # Parse request
                    try:
                        request = json.loads(message)
                        command = request.get("command", "")
                        params = request.get("params", {})
                    except json.JSONDecodeError:
                        response = {"status": "error", "message": "Invalid JSON"}
                        self._socket.send_string(json.dumps(response))
                        continue
                    
                    # Handle request
                    if self.command_handler:
                        try:
                            result = self.command_handler(command, params)
                            response = {"status": "ok", "result": result}
                        except Exception as e:
                            response = {"status": "error", "message": str(e)}
                    else:
                        response = {"status": "error", "message": "No command handler"}
                    
                    self._socket.send_string(json.dumps(response))
                    
            except zmq.ZMQError as e:
                if self._running:
                    logger.error(f"ZMQ RPC error: {e}")
            except Exception as e:
                if self._running:
                    logger.error(f"RPC server error: {e}")
    
    def __repr__(self):
        status = "running" if self._running else "stopped"
        return f"<ZmqRpcServer port={self.port} status={status}>"


class ZmqBridge:
    """
    Unified ZMQ bridge combining Publisher and RPC Server.
    
    This is the main interface for TUI ↔ Web communication.
    """
    
    def __init__(
        self,
        pub_port: int = 5555,
        rpc_port: int = 5556,
        command_handler: Optional[Callable[[str, Dict], Dict]] = None
    ):
        self.publisher = ZmqPublisher(port=pub_port)
        self.rpc_server = ZmqRpcServer(port=rpc_port, command_handler=command_handler)
        self._started = False
        
    def start(self) -> bool:
        """Start both publisher and RPC server."""
        pub_ok = self.publisher.start()
        rpc_ok = self.rpc_server.start()
        self._started = pub_ok and rpc_ok
        return self._started
    
    def stop(self):
        """Stop both publisher and RPC server."""
        self.publisher.stop()
        self.rpc_server.stop()
        self._started = False
    
    def publish(self, topic: str, data: Any) -> bool:
        """Publish an event."""
        return self.publisher.publish(topic, data)
    
    def set_command_handler(self, handler: Callable[[str, Dict], Dict]):
        """Set the RPC command handler."""
        self.rpc_server.set_command_handler(handler)
    
    @property
    def is_running(self) -> bool:
        return self._started
    
    def __repr__(self):
        return f"<ZmqBridge publisher={self.publisher} rpc={self.rpc_server}>"


# Global bridge instance (singleton pattern)
_global_bridge: Optional[ZmqBridge] = None


def get_zmq_bridge() -> Optional[ZmqBridge]:
    """Get the global ZMQ bridge instance."""
    return _global_bridge


def init_zmq_bridge(
    pub_port: int = 5555,
    rpc_port: int = 5556,
    command_handler: Optional[Callable[[str, Dict], Dict]] = None
) -> ZmqBridge:
    """Initialize and return the global ZMQ bridge."""
    global _global_bridge
    
    if _global_bridge is None:
        _global_bridge = ZmqBridge(
            pub_port=pub_port,
            rpc_port=rpc_port,
            command_handler=command_handler
        )
    
    return _global_bridge


def start_zmq_bridge() -> bool:
    """Start the global ZMQ bridge."""
    bridge = get_zmq_bridge()
    if bridge:
        return bridge.start()
    return False


def stop_zmq_bridge():
    """Stop the global ZMQ bridge."""
    bridge = get_zmq_bridge()
    if bridge:
        bridge.stop()