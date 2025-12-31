"""WebSocket connection manager and handler functions."""

import json
from datetime import datetime
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections for broadcasting."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str, user_id: str = None):
        """Send a JSON string message to all connected clients."""
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                disconnected_connections.append(connection)
        
        for connection in disconnected_connections:
            self.disconnect(connection)

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

manager = ConnectionManager()