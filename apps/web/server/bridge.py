import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# Add vendored dependencies to path BEFORE third-party imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deps'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import zmq
import zmq.asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orbital-bridge")

app = FastAPI()

# Configuration
ZMQ_ADDR = os.getenv("JCAPY_ZMQ_ADDR", "tcp://localhost:5555")
RPC_ADDR = os.getenv("JCAPY_RPC_ADDR", "tcp://localhost:5556")
AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "orbital_audit.jsonl")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active sessions: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active sessions: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

def log_event_to_glass_box(event):
    """Writes event to a local JSONL file for auditability (One-Army Glass-Box)."""
    try:
        # Using a simple append for the audit log
        with open(AUDIT_LOG_PATH, "a") as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "topic": event.get("topic"),
                "event": event.get("data")
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Audit Log Error: {e}")

async def zmq_listener():
    """Listens to ZeroMQ events from jcapyd and broadcasts them to WebSockets."""
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(ZMQ_ADDR)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    logger.info(f"Connected to jcapyd ZMQ stream at {ZMQ_ADDR}")
    logger.info(f"Audit Persistence active at {AUDIT_LOG_PATH}")

    try:
        while True:
            # Multi-part message support [topic, payload]
            msg = await subscriber.recv_multipart()
            topic = msg[0].decode('utf-8')
            payload = msg[1].decode('utf-8')

            logger.debug(f"Received ZMQ message: {topic}")

            event = {
                "topic": topic,
                "data": json.loads(payload) if payload.startswith('{') else payload
            }

            # Scalability Hardening: Audit Persistence
            log_event_to_glass_box(event)

            await manager.broadcast(json.dumps(event))
    except Exception as e:
        logger.error(f"ZMQ Listener Error: {e}")
    finally:
        subscriber.close()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(zmq_listener())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")

            # Handle commands from the Web UI (e.g., APPROVE_ACTION)
            try:
                msg = json.loads(data)
                if msg.get("type") == "APPROVE_ACTION":
                    await handle_approval_rpc(msg.get("id"), msg.get("approved"))
            except Exception as e:
                logger.error(f"Failed to process client command: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_approval_rpc(event_id: str, approved: bool):
    """Sends an approval decision back to jcapyd via a Request socket."""
    context = zmq.asyncio.Context()
    request = context.socket(zmq.REQ)
    request.connect(RPC_ADDR)

    logger.info(f"Sending approval RPC to {RPC_ADDR}: ID={event_id}, Approved={approved}")

    payload = json.dumps({"event_id": event_id, "approved": approved})
    await request.send_string(payload)

    # Wait for ack
    reply = await request.recv_string()
    logger.info(f"jcapyd reply: {reply}")
    request.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
