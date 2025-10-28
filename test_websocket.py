import websockets
import asyncio
import json
import time

async def test_websocket():
    print("Testing WebSocket connection...")
    
    try:
        # Connect to WebSocket
        async with websockets.connect("ws://localhost:8000/ws/alerts") as websocket:
            print("Connected to WebSocket server")
            
            # Test sending a message
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"Server response: {response}")
            
            # Listen for incoming alerts for 30 seconds
            print(" Listening for real-time alerts (30 seconds)...")
            start_time = time.time()
            
            while time.time() - start_time < 30:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    alert_data = json.loads(message)
                    print(f"NEW ALERT RECEIVED: {alert_data}")
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
                    
    except Exception as e:
        print(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())