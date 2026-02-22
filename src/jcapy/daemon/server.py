# SPDX-License-Identifier: Apache-2.0
"""
JCapy Daemon Server

A lightweight HTTP server providing:
- Web Control Plane UI
- Health check endpoints
- REST API for daemon control
- WebSocket for real-time updates
- ZMQ bridge for TUI ↔ Web communication
"""

import os
import sys
import json
import signal
import threading
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
from pathlib import Path

from jcapy.core.service import get_service
from jcapy.core.base import CommandResult
from jcapy.utils.updates import VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jcapyd')

# Try to import grpc for the Orbital Architecture
try:
    import grpc
    from concurrent import futures
    from jcapy.core.proto import jcapy_pb2
    from jcapy.core.proto import jcapy_pb2_grpc
    from jcapy.core.ssl_utils import get_grpc_credentials
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("grpcio not installed or proto files missing. gRPC interface will be disabled.")

# ZMQ Bridge integration
_zmq_bridge = None
_command_queue = []  # Queue for commands from Web UI


class DaemonState:
    """Shared daemon state"""

    def __init__(self):
        self.start_time = datetime.now()
        self.status = "running"
        self.active_sessions = 0
        self.tasks_completed = 0
        self.last_activity = datetime.now()
        self._lock = threading.Lock()

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            return {
                "status": self.status,
                "uptime_seconds": int(uptime),
                "uptime_human": self._format_uptime(uptime),
                "active_sessions": self.active_sessions,
                "tasks_completed": self.tasks_completed,
                "last_activity": self.last_activity.isoformat(),
                "version": VERSION
            }

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime in human-readable format"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def record_activity(self):
        with self._lock:
            self.last_activity = datetime.now()

    def increment_task(self):
        with self._lock:
            self.tasks_completed += 1
            self.last_activity = datetime.now()


# Global state
state = DaemonState()


class ControlPlaneHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Control Plane"""

    # Suppress default logging
    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

    def _send_json(self, data: Dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _send_html(self, html: str, status: int = 200):
        """Send HTML response"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        """Handle GET requests"""
        state.record_activity()

        if self.path == '/health':
            self._handle_health()
        elif self.path == '/api/status':
            self._handle_status()
        elif self.path == '/api/metrics':
            self._handle_metrics()
        elif self.path == '/' or self.path == '':
            self._handle_index()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests"""
        state.record_activity()

        if self.path == '/api/command':
            self._handle_command()
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_health(self):
        """Health check endpoint"""
        self._send_json({
            "status": "healthy",
            "service": "jcapyd",
            "version": VERSION,
            "timestamp": datetime.now().isoformat()
        })

    def _handle_status(self):
        """Detailed status endpoint"""
        self._send_json(state.to_dict())

    def _handle_metrics(self):
        """Prometheus-style metrics endpoint"""
        metrics = state.to_dict()
        output = [
            f"# HELP jcapy_uptime_seconds Daemon uptime in seconds",
            f"# TYPE jcapy_uptime_seconds counter",
            f"jcapy_uptime_seconds {metrics['uptime_seconds']}",
            f"",
            f"# HELP jcapy_tasks_completed Total tasks completed",
            f"# TYPE jcapy_tasks_completed counter",
            f"jcapy_tasks_completed {metrics['tasks_completed']}",
            f"",
            f"# HELP jcapy_active_sessions Active sessions",
            f"# TYPE jcapy_active_sessions gauge",
            f"jcapy_active_sessions {metrics['active_sessions']}",
        ]

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write('\n'.join(output).encode())

    def _handle_index(self):
        """Serve the Control Plane UI"""
        html = self._get_control_plane_html()
        self._send_html(html)

    def _handle_command(self):
        """Handle command execution"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            command = data.get('command', '')
            if not command:
                return self._send_json({"error": "No command provided"}, 400)

            # Execute command (simplified - in production, use proper sandboxing)
            state.increment_task()

            self._send_json({
                "status": "accepted",
                "command": command,
                "message": f"Command '{command}' queued for execution"
            })

        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _get_control_plane_html(self) -> str:
        """Generate the Control Plane HTML UI"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JCapy Control Plane</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        }
        .logo { font-size: 1.5rem; font-weight: bold; color: #22d3ee; }
        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(34, 197, 94, 0.2);
            border-radius: 20px;
            border: 1px solid #22c55e;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            background: #22c55e;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        /* Cards */
        .card {
            background: rgba(30, 41, 59, 0.6);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
            backdrop-filter: blur(10px);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #334155;
        }
        .card-title { font-size: 1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .card-value { font-size: 2rem; font-weight: bold; color: #22d3ee; }

        /* Stats */
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        }
        .stat-label { color: #94a3b8; }
        .stat-value { color: #e2e8f0; font-weight: 500; }

        /* Terminal */
        .terminal {
            background: #0f172a;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
            font-size: 0.9rem;
        }
        .terminal-header {
            display: flex;
            gap: 8px;
            margin-bottom: 15px;
        }
        .terminal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .terminal-dot.red { background: #ef4444; }
        .terminal-dot.yellow { background: #eab308; }
        .terminal-dot.green { background: #22c55e; }
        .terminal-content {
            color: #94a3b8;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .terminal-prompt { color: #22d3ee; }
        .terminal-command { color: #e2e8f0; }

        /* Commands */
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        .cmd-btn {
            padding: 12px 16px;
            background: rgba(34, 211, 238, 0.1);
            border: 1px solid #22d3ee;
            border-radius: 8px;
            color: #22d3ee;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .cmd-btn:hover {
            background: rgba(34, 211, 238, 0.2);
            transform: translateY(-2px);
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 20px;
            color: #64748b;
            font-size: 0.85rem;
        }
        .footer a { color: #22d3ee; text-decoration: none; }

        /* Responsive */
        @media (max-width: 768px) {
            .header { flex-direction: column; gap: 15px; text-align: center; }
            .card-value { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">🚀 JCapy Control Plane</div>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span>Daemon Running</span>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Uptime</span>
                    <span>⏱️</span>
                </div>
                <div class="card-value" id="uptime">--</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Tasks Completed</span>
                    <span>✅</span>
                </div>
                <div class="card-value" id="tasks">0</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Version</span>
                    <span>📦</span>
                </div>
                <div class="card-value">''' + VERSION + '''</div>
            </div>
        </div>

        <!-- Status Card -->
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
                <span class="card-title">Daemon Status</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Status</span>
                <span class="stat-value" style="color: #22c55e;">● Running</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Mode</span>
                <span class="stat-value">Background Daemon</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Web Port</span>
                <span class="stat-value">8080</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Last Activity</span>
                <span class="stat-value" id="last-activity">--</span>
            </div>
        </div>

        <!-- Terminal -->
        <div class="terminal" style="margin-bottom: 20px;">
            <div class="terminal-header">
                <div class="terminal-dot red"></div>
                <div class="terminal-dot yellow"></div>
                <div class="terminal-dot green"></div>
            </div>
            <div class="terminal-content">
<span class="terminal-prompt">$</span> <span class="terminal-command">jcapy --help</span>
  One-Army Orchestrator • Build Like a Team of Ten

<span class="terminal-prompt">$</span> <span class="terminal-command">jcapy doctor</span>
  ✓ All systems operational

<span class="terminal-prompt">$</span> <span class="terminal-command">jcapy manage</span>
  🎮 Launching TUI Dashboard...

<span class="terminal-prompt">$</span> <span class="terminal-command">docker exec -it jcapy-daemon jcapy --help</span>
  Access JCapy CLI inside Docker container
            </div>
        </div>

        <!-- Quick Commands -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Quick Commands</span>
            </div>
            <div class="commands-grid">
                <button class="cmd-btn" onclick="copyCmd('docker exec -it jcapy-daemon jcapy --help')">
                    📋 jcapy --help
                </button>
                <button class="cmd-btn" onclick="copyCmd('docker exec -it jcapy-daemon jcapy doctor')">
                    🏥 jcapy doctor
                </button>
                <button class="cmd-btn" onclick="copyCmd('docker exec -it jcapy-daemon jcapy manage')">
                    🎮 jcapy manage
                </button>
                <button class="cmd-btn" onclick="copyCmd('docker-compose logs -f jcapy')">
                    📜 View Logs
                </button>
                <button class="cmd-btn" onclick="copyCmd('docker-compose restart jcapy')">
                    🔄 Restart Daemon
                </button>
                <button class="cmd-btn" onclick="copyCmd('curl http://localhost:8080/health')">
                    ❤️ Health Check
                </button>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>JCapy v''' + VERSION + ''' • <a href="https://github.com/ponli550/JCapy">GitHub</a> • One-Army Movement ❤️</p>
        </div>
    </div>

    <script>
        // Fetch status
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                document.getElementById('uptime').textContent = data.uptime_human;
                document.getElementById('tasks').textContent = data.tasks_completed;
                document.getElementById('last-activity').textContent =
                    new Date(data.last_activity).toLocaleTimeString();
            } catch (e) {
                console.error('Failed to fetch status:', e);
            }
        }

        // Copy command to clipboard
        function copyCmd(cmd) {
            navigator.clipboard.writeText(cmd).then(() => {
                alert('Copied: ' + cmd);
            });
        }

        // Update every 5 seconds
        fetchStatus();
        setInterval(fetchStatus, 5000);
    </script>
</body>
</html>'''


class DaemonServer:
    """JCapy Daemon Server"""

    def __init__(self, port: int = 8080, grpc_port: int = 50051, host: str = '0.0.0.0'):
        self.port = port
        self.grpc_port = grpc_port
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.grpc_server = None
        self._shutdown = False

    def start(self):
        """Start the daemon server"""
        logger.info(f"Starting JCapy Daemon on {self.host}:{self.port} (HTTP) and {self.grpc_port} (gRPC)")

        self.server = HTTPServer((self.host, self.port), ControlPlaneHandler)

        # Start gRPC server if available
        if GRPC_AVAILABLE:
            try:
                self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
                jcapy_pb2_grpc.add_JCapyOrchestratorServicer_to_server(JCapyServicer(), self.grpc_server)

                # Secure gRPC with mTLS
                try:
                    from jcapy.core.ssl_utils import get_grpc_credentials
                    credentials = get_grpc_credentials(is_server=True)
                    self.grpc_server.add_secure_port(f'[::]:{self.grpc_port}', credentials)
                    logger.info(f"🧠 JCapy Brain (gRPC SECURE mTLS) active at [::]:{self.grpc_port}")
                except Exception as e:
                    logger.warning(f"Failed to initialize mTLS: {e}. Falling back to insecure port for local dev.")
                    self.grpc_server.add_insecure_port(f'[::]:{self.grpc_port}')
                    logger.info(f"🧠 JCapy Brain (gRPC INSECURE) active at [::]:{self.grpc_port}")

                self.grpc_server.start()
            except Exception:
                logger.exception("Failed to start gRPC server")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"🚀 JCapy Control Plane active at http://localhost:{self.port}")
        logger.info(f"❤️  Health check: http://localhost:{self.port}/health")
        logger.info(f"📊 Metrics: http://localhost:{self.port}/api/metrics")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def stop(self):
        """Stop the daemon server"""
        if self.server:
            logger.info("Stopping JCapy Daemon...")
            state.status = "stopping"

            if self.grpc_server:
                self.grpc_server.stop(0)
                logger.info("gRPC server stopped")

            self.server.shutdown()
            self.server = None
            logger.info("JCapy Daemon stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()


def _init_zmq_bridge():
    """Initialize ZMQ bridge for TUI ↔ Web communication."""
    global _zmq_bridge
    try:
        from jcapy.core.zmq_publisher import init_zmq_bridge, start_zmq_bridge
        from jcapy.core.bus import attach_zmq_to_bus

        # Create bridge with command handler
        _zmq_bridge = init_zmq_bridge(
            pub_port=5555,
            rpc_port=5556,
            command_handler=_handle_rpc_command
        )

        if start_zmq_bridge():
            logger.info("✅ ZMQ Bridge started on ports 5555 (PUB) and 5556 (RPC)")
            attach_zmq_to_bus()

            # Start heartbeat thread
            _start_heartbeat()
            return True
        else:
            logger.warning("⚠️ ZMQ Bridge failed to start")
            return False
    except ImportError as e:
        logger.warning(f"⚠️ ZMQ not available: {e}")
        return False


def _handle_rpc_command(command: str, params: dict) -> dict:
    """
    Handle RPC commands from Web UI (via ZMQ).
    """
    logger.info(f"Received ZMQ RPC command: {command}")

    service = get_service()

    if command == "EXECUTE_COMMAND":
        cmd_str = params.get("command", "")
        if cmd_str:
            # Execute via Service Layer
            result = service.execute(cmd_str, tui_data=params.get("tui_data"))
            state.increment_task()
            return {
                "status": "success" if result.status == "success" else "failure",
                "message": result.message,
                "result": str(result.data) if result.data else None
            }
        return {"status": "error", "message": "No command provided"}

    # ... (other cases simplified for now)
    elif command == "GET_STATUS":
        return state.to_dict()

    return {"status": "error", "message": f"Unknown command: {command}"}

# ------------------------------------------------------------------
# gRPC Servicer (JCapy 2.0 Brain)
# ------------------------------------------------------------------

class JCapyServicer(jcapy_pb2_grpc.JCapyOrchestratorServicer):
    """
    Implementation of JCapyOrchestrator gRPC service.
    This is the primary interface for JCapy 2.0.
    """
    def __init__(self):
        self.service = get_service()

    def ExecuteCommand(self, request, context):
        logger.info(f"gRPC ExecuteCommand: {request.command_str}")
        result = self.service.execute(request.command_str, tui_data=dict(request.context))
        state.increment_task()

        return jcapy_pb2.CommandResponse(
            status="success" if result.status == "success" else "failure",
            message=result.message,
            result_data_json=json.dumps(result.data) if hasattr(result, 'data') and result.data else "{}"
        )

    def GetStatus(self, request, context):
        s = state.to_dict()
        from jcapy.config import get_current_persona_name
        return jcapy_pb2.StatusResponse(
            status=s["status"],
            version=s["version"],
            uptime_seconds=s["uptime_seconds"],
            active_persona=get_current_persona_name()
        )

    def StreamLogs(self, request, context):
        """Stream logs from the service bus via gRPC."""
        from jcapy.core.bus import get_event_bus
        bus = get_event_bus()

        queue = []
        lock = threading.Lock()
        event = threading.Event()

        def on_log(payload):
            with lock:
                queue.append(payload)
                event.set()

        # Subscribe to terminal output and audit logs
        bus.subscribe("TERMINAL_OUTPUT", on_log)
        bus.subscribe("AUDIT_LOG", on_log)

        try:
            while context.is_active():
                if event.wait(timeout=1.0):
                    with lock:
                        items = list(queue)
                        queue.clear()
                        event.clear()

                    for item in items:
                        # Convert to LogEntry
                        yield jcapy_pb2.LogEntry(
                            source=item.get("source", "daemon"),
                            level=item.get("level", "info"),
                            message=item.get("line") or item.get("message") or str(item),
                            timestamp=item.get("timestamp", datetime.now().isoformat())
                        )
        finally:
            # Unsubscribe would be nice, but bus doesn't support it yet in a simple way
            # We'll just ignore for now as it's a POC/Alpha
            pass


def _start_heartbeat():
    """Start background heartbeat thread for daemon health monitoring."""
    def heartbeat_loop():
        while True:
            try:
                if _zmq_bridge and _zmq_bridge.is_running:
                    _zmq_bridge.publish("HEARTBEAT", {
                        "timestamp": datetime.now().isoformat(),
                        "status": state.to_dict()
                    })
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            import time
            time.sleep(30)  # Heartbeat every 30 seconds

    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()
    logger.info("Heartbeat thread started (30s interval)")


def get_pending_commands() -> list:
    """Get and clear pending commands from Web UI."""
    global _command_queue
    commands = _command_queue.copy()
    _command_queue.clear()
    return commands


def run_daemon(port: int = 8080, with_zmq: bool = True):
    """Entry point for running the daemon"""
    # Initialize ZMQ bridge first
    if with_zmq:
        _init_zmq_bridge()

    server = DaemonServer(port=port)
    server.start()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='JCapy Daemon Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')

    args = parser.parse_args()

    server = DaemonServer(port=args.port, host=args.host)
    server.start()
