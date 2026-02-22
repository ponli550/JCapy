import sys
import os
import time
import json

# Add vendored dependencies to path BEFORE third-party imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deps'))

import zmq

ZMQ_ADDR = "tcp://*:5555"
RPC_ADDR = "tcp://*:5556"

def simulate():
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(ZMQ_ADDR)

    replier = context.socket(zmq.REP)
    replier.bind(RPC_ADDR)

    print(f"🚀 Mock jcapyd active (Looping).")
    print(f"📡 Publishing to {ZMQ_ADDR}")
    print(f"📥 Awaiting RPCs at {RPC_ADDR}")

    events = [
        {"type": "THOUGHT", "message": "Analyzing project structure...", "timestamp": "11:30:00"},
        {"type": "ACTION", "message": "Reading pyproject.toml", "timestamp": "11:30:05"},
        {"type": "INTERVENTION", "id": "tx_loop", "tool": "WRITE_FILE", "path": "src/main.py", "diff": "- version = \"1.0\"\n+ version = \"2.0\"", "timestamp": "11:30:10"}
    ]

    # Wait for bridge to connect
    time.sleep(2)

    while True:
        for event in events:
            # Update ID for each loop to avoid UI state collisions
            loop_id = f"tx_{int(time.time())}"
            current_event = {**event}
            if current_event['type'] == 'INTERVENTION':
                current_event['id'] = loop_id

            print(f"Sending event: {current_event['type']}")
            try:
                publisher.send_multipart([b"trajectory", json.dumps(current_event).encode('utf-8')])
            except Exception as e:
                print(f"Send Error: {e}")

            if current_event['type'] == 'INTERVENTION':
                print(f"Halted. Waiting for Operator Approval for {loop_id}...")
                # Use a timeout so we don't hang forever if no one is watching
                if replier.poll(timeout=10000): # 10 second timeout
                    try:
                        request = replier.recv_string()
                        print(f"Received RPC request: {request}")
                        replier.send_string("ACK_SUCCESS")

                        # Send follow-up success
                        publisher.send_multipart([b"trajectory", json.dumps({
                            "type": "SUCCESS",
                            "message": "Action approved and executed.",
                            "timestamp": time.strftime("%H:%M:%S")
                        }).encode('utf-8')])
                    except Exception as e:
                        print(f"RPC Handling Error: {e}")
                else:
                    print("No approval received within timeout. Continuing loop...")

            time.sleep(3)
        time.sleep(2)

if __name__ == "__main__":
    try:
        simulate()
    except KeyboardInterrupt:
        print("\nShutdown.")
