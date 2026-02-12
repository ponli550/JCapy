import subprocess
import json
import time
import sys
import os

def send_message(proc, msg):
    """Send a JSON-RPC message to the server's stdin."""
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()

def read_message(proc):
    """Read a JSON-RPC message from the server's stdout."""
    line = proc.stdout.readline()
    if not line:
        return None
    try:
        return json.loads(line.decode())
    except json.JSONDecodeError:
        return line.decode()

def verify():
    print("🚀 Starting JCapy MCP Verification...")

    # Run the server as a subprocess
    # We use 'python3 -m jcapy.main mcp' assuming jcapy is installed or in PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

    cmd = [sys.executable, "-m", "jcapy.main", "mcp"]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )

    time.sleep(1) # Wait for server to start

    try:
        # 1. Send Initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "verify-script", "version": "1.0"}
            }
        }
        send_message(proc, init_msg)
        resp = read_message(proc)
        print(f"✅ Initialize Response: {json.dumps(resp, indent=2)}")

        # 2. List Tools
        list_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        send_message(proc, list_msg)
        resp = read_message(proc)
        print(f"✅ Tools List: {json.dumps(resp, indent=2)}")

        # 3. Call tool list_skills
        call_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_skills",
                "arguments": {}
            }
        }
        send_message(proc, call_msg)
        resp = read_message(proc)
        print(f"✅ list_skills Output: {json.dumps(resp, indent=2)}")

    finally:
        proc.terminate()
        print("🛑 Verification finished.")

if __name__ == "__main__":
    verify()
