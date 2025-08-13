#!/usr/bin/env python3
"""
Test WebSocket connection status flow to debug frontend connection issues.
This will help identify if the issue is with status transitions or frontend logic.
"""

import asyncio
import websockets
import json
import time

async def test_websocket_status():
    uri = "ws://localhost:8000/ws/updates"
    
    print("🔍 Testing WebSocket status flow...")
    print(f"Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            print(f"   Connection state: {websocket.state}")
            print(f"   Local address: {websocket.local_address}")
            print(f"   Remote address: {websocket.remote_address}")
            
            # Send a test message to trigger response
            test_message = {
                "type": "test",
                "data": "connection_status_check",
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")
            
            # Listen for messages for a few seconds
            print("\n📥 Listening for messages...")
            start_time = time.time()
            message_count = 0
            
            try:
                while time.time() - start_time < 10:  # Listen for 10 seconds
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        message_count += 1
                        parsed = json.loads(message)
                        print(f"   Message {message_count}: {parsed.get('type', 'unknown')} - {parsed}")
                    except asyncio.TimeoutError:
                        print("   (waiting for messages...)")
                        continue
                        
            except websockets.exceptions.ConnectionClosed:
                print("❌ WebSocket connection closed by server")
                
            print(f"\n📊 Summary:")
            print(f"   Total messages received: {message_count}")
            print(f"   Connection duration: {time.time() - start_time:.1f}s")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running on port 8000?")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_status())
