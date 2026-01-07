from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    """Manages active WebSocket connections for broadcasting."""
    def __init__(self):
        # Store connections keyed by user_id
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Add a new WebSocket connection for a specific user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected for user {user_id}. Total: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        """Remove a WebSocket connection for a user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        print(f"WebSocket disconnected for user {user_id}. Total: {len(self.active_connections)}")

    async def send_to_user(self, message: str, user_id: str):
        """Send a message only to the specified user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                self.disconnect(user_id)

    async def send_connection_message(self, websocket: WebSocket):
        """Send initial connection confirmation message."""
        await websocket.send_text(json.dumps({
            "type": "system",
            "message": "Connected to OBEX Alert System"
        }))

    async def send_pong(self, websocket: WebSocket):
        """Send pong response to keep-alive message."""
        await websocket.send_text(json.dumps({
            "type": "pong",
            "message": "Connection active",
            "timestamp": datetime.utcnow().isoformat()
        }))

# Create instance
manager = ConnectionManager()
