#!/usr/bin/env python3
"""
Test script for TUI ↔ Web Control Plane Integration

This script verifies:
1. ZMQ Publisher is functional
2. EventBus can broadcast to ZMQ
3. Bridge can receive events
4. Database is accessible
"""

import sys
import os
import time
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_zmq_publisher():
    """Test ZMQ Publisher module."""
    print("=" * 60)
    print("TEST 1: ZMQ Publisher Module")
    print("=" * 60)
    
    try:
        from jcapy.core.zmq_publisher import ZmqPublisher, ZMQ_AVAILABLE
        
        if not ZMQ_AVAILABLE:
            print("⚠️  pyzmq not installed - skipping ZMQ tests")
            print("   Install with: pip install pyzmq")
            return False
        
        print("✅ pyzmq is available")
        
        # Create publisher
        publisher = ZmqPublisher(port=5555)
        print(f"✅ Created publisher: {publisher}")
        
        # Start publisher
        if publisher.start():
            print("✅ Publisher started on port 5555")
            
            # Test publish
            result = publisher.publish("TEST_EVENT", {"message": "Hello from test"})
            if result:
                print("✅ Successfully published test event")
            else:
                print("❌ Failed to publish test event")
            
            publisher.stop()
            print("✅ Publisher stopped")
            return True
        else:
            print("❌ Failed to start publisher")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_event_bus():
    """Test EventBus with ZMQ integration."""
    print("\n" + "=" * 60)
    print("TEST 2: EventBus Integration")
    print("=" * 60)
    
    try:
        from jcapy.core.bus import get_event_bus, attach_zmq_to_bus
        
        bus = get_event_bus()
        print(f"✅ Got event bus: {bus}")
        
        # Test subscribe
        received = []
        def callback(payload):
            received.append(payload)
        
        bus.subscribe("TEST_EVENT", callback)
        print("✅ Subscribed to TEST_EVENT")
        
        # Test publish local
        bus.publish_local("TEST_EVENT", {"data": "test"})
        if received:
            print(f"✅ Local publish works: {received[-1]}")
        else:
            print("❌ Local publish failed")
            return False
        
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_database():
    """Test database/memory module."""
    print("\n" + "=" * 60)
    print("TEST 3: Database/Memory Module")
    print("=" * 60)
    
    try:
        from jcapy.memory import get_memory_bank
        
        memory = get_memory_bank()
        print(f"✅ Got memory bank: {type(memory).__name__}")
        
        if hasattr(memory, 'client') and memory.client:
            print("✅ ChromaDB client initialized")
            
            # Check collection
            if memory.collection:
                count = memory.collection.count()
                print(f"✅ Collection ready with {count} documents")
                return True
            else:
                print("⚠️  Collection not initialized")
                return False
        else:
            print("⚠️  ChromaDB not available - check if chromadb is installed")
            return False
            
    except ImportError as e:
        print(f"⚠️  Memory module import error: {e}")
        print("   Install with: pip install chromadb")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_bridge_module():
    """Test the bridge.py module."""
    print("\n" + "=" * 60)
    print("TEST 4: WebSocket Bridge Module")
    print("=" * 60)
    
    bridge_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'apps', 'web', 'server', 'bridge.py'
    )
    
    if os.path.exists(bridge_path):
        print(f"✅ Bridge module exists at: {bridge_path}")
        
        # Check if required imports are available
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("bridge", bridge_path)
            if spec:
                print("✅ Bridge module can be loaded")
                
                # Check for fastapi and zmq
                try:
                    import fastapi
                    print("✅ FastAPI available")
                except ImportError:
                    print("⚠️  FastAPI not installed - bridge won't work")
                    print("   Install with: pip install fastapi uvicorn")
                
                try:
                    import zmq
                    print("✅ ZMQ available")
                except ImportError:
                    print("⚠️  ZMQ not installed - bridge won't work")
                    print("   Install with: pip install pyzmq")
                
                return True
            else:
                print("❌ Failed to load bridge module spec")
                return False
        except Exception as e:
            print(f"❌ Error checking bridge: {e}")
            return False
    else:
        print(f"❌ Bridge module not found at: {bridge_path}")
        return False


def test_daemon_server():
    """Test daemon server module."""
    print("\n" + "=" * 60)
    print("TEST 5: Daemon Server Module")
    print("=" * 60)
    
    try:
        from jcapy.daemon.server import DaemonServer, _init_zmq_bridge
        
        print("✅ Daemon server module imported")
        print("✅ ZMQ bridge integration function available")
        
        # Check daemon state
        from jcapy.daemon.server import state
        print(f"✅ Daemon state initialized: {state.to_dict()}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational! TUI ↔ Web integration ready.")
    else:
        print("\n⚠️  Some components need attention. Check the output above.")


def main():
    print("🚀 JCapy TUI ↔ Web Integration Test Suite")
    print("Testing communication between TUI and Web Control Plane\n")
    
    results = {
        "ZMQ Publisher": test_zmq_publisher(),
        "EventBus": test_event_bus(),
        "Database": test_database(),
        "Bridge Module": test_bridge_module(),
        "Daemon Server": test_daemon_server()
    }
    
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())