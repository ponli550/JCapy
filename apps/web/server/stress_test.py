import sys
import os
import json
import time

# Add vendored dependencies to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deps'))
import zmq

# Default ZMQ address for jcapyd
ZMQ_ADDR = "tcp://127.0.0.1:5555"

def run_stress_test(count=2000):
    """Sends a high-frequency stream of mock events to the bridge."""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    # We bind because the bridge connects to us
    try:
        socket.bind(ZMQ_ADDR)
    except Exception as e:
        print(f"Error binding to {ZMQ_ADDR}: {e}. Ensure simulate_daemon.py is stopped.")
        return

    print(f"🚀 [STRESS TEST] Purging {count} events to {ZMQ_ADDR}...")
    time.sleep(2) # Stability pause

    start_time = time.time()
    for i in range(count):
        topic = "THOUGHT"
        payload = {
            "type": "THOUGHT",
            "message": f"High-density reasoning frame {i} // AUDIT_TICK_{i}",
            "timestamp": time.strftime("%H:%M:%S")
        }

        # Non-blocking send
        socket.send_multipart([
            topic.encode('utf-8'),
            json.dumps(payload).encode('utf-8')
        ])

        # Small sleep every 100 events to prevent pipe saturation
        if i % 100 == 0:
            time.sleep(0.01)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"✅ [STRESS TEST] Complete. {count} events sent in {total_time:.2f}s (~{count/total_time:.0f} msg/sec).")
    print("Check the Web UI for fluidity and 'orbital_audit.jsonl' for persistence.")
    socket.close()

if __name__ == "__main__":
    run_stress_test()
