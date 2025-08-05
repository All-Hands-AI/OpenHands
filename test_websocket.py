#!/usr/bin/env python3
"""
WebSocket Connection Test Script for OpenHands

This script tests the WebSocket connection to ensure proper setup.
"""

import asyncio
import json
import sys
from typing import Any, Dict

import socketio


class WebSocketTester:
    def __init__(self, host: str = "localhost", port: int = 12000):
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.events_received = []

    async def setup_handlers(self):
        """Set up event handlers for testing."""
        
        @self.sio.event
        async def connect():
            print("✅ Connected to WebSocket server")
            self.connected = True

        @self.sio.event
        async def disconnect():
            print("❌ Disconnected from WebSocket server")
            self.connected = False

        @self.sio.event
        async def connect_error(data):
            print(f"❌ Connection error: {data}")

        @self.sio.event
        async def oh_event(data):
            print(f"📨 Received oh_event: {json.dumps(data, indent=2)}")
            self.events_received.append(data)

    async def test_connection(self) -> bool:
        """Test basic WebSocket connection."""
        try:
            print(f"🔌 Attempting to connect to {self.url}...")
            
            # Add query parameters that OpenHands expects
            query = {
                'conversation_id': 'test-conversation',
                'latest_event_id': -1,
                'providers_set': '',
            }
            
            await self.sio.connect(
                self.url,
                transports=['websocket'],
                wait_timeout=10,
                query=query
            )
            
            # Wait a moment to ensure connection is established
            await asyncio.sleep(2)
            
            if self.connected:
                print("✅ WebSocket connection successful!")
                return True
            else:
                print("❌ WebSocket connection failed!")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed with error: {e}")
            return False

    async def test_event_sending(self) -> bool:
        """Test sending events to the server."""
        if not self.connected:
            print("❌ Cannot test event sending - not connected")
            return False

        try:
            print("📤 Testing event sending...")
            
            # Send a test event
            test_event = {
                "action": "message",
                "args": {
                    "content": "Hello from WebSocket test!",
                    "wait_for_response": False
                }
            }
            
            await self.sio.emit('oh_user_action', test_event)
            print("✅ Test event sent successfully!")
            
            # Wait for potential response
            await asyncio.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ Event sending failed: {e}")
            return False

    async def cleanup(self):
        """Clean up the connection."""
        if self.connected:
            await self.sio.disconnect()
        print("🧹 Cleanup completed")

    async def run_tests(self) -> bool:
        """Run all WebSocket tests."""
        print("🧪 Starting WebSocket tests...\n")
        
        await self.setup_handlers()
        
        # Test 1: Basic connection
        connection_success = await self.test_connection()
        if not connection_success:
            await self.cleanup()
            return False
        
        # Test 2: Event sending
        event_success = await self.test_event_sending()
        
        # Cleanup
        await self.cleanup()
        
        # Summary
        print("\n📊 Test Results:")
        print(f"  Connection: {'✅ PASS' if connection_success else '❌ FAIL'}")
        print(f"  Event Sending: {'✅ PASS' if event_success else '❌ FAIL'}")
        print(f"  Events Received: {len(self.events_received)}")
        
        return connection_success and event_success


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenHands WebSocket connection")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=12000, help="WebSocket server port")
    
    args = parser.parse_args()
    
    print("🚀 OpenHands WebSocket Connection Tester")
    print("=" * 50)
    
    tester = WebSocketTester(args.host, args.port)
    
    try:
        success = await tester.run_tests()
        
        if success:
            print("\n🎉 All tests passed! WebSocket setup is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Check the WebSocket configuration.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        await tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        await tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())