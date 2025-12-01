"""WebSocket endpoint handlers."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import manager

router = APIRouter(
    tags=["WebSocket"]
)


@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications.
    Handles client connections, disconnections, and keep-alive messages.
    """
    await manager.connect(websocket)
    print(f"New WebSocket connection established. Active connections: {len(manager.active_connections)}")
    
    try:
        await manager.send_connection_message(websocket)
        
        while True:
            # Handle keep-alive messages
            await websocket.receive_text()
            await manager.send_pong(websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket disconnected. Remaining connections: {len(manager.active_connections)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        print(f"Connection terminated. Remaining connections: {len(manager.active_connections)}")


@router.get("/websocket-info", summary="WebSocket Connection Details")
async def get_websocket_info():
    """
    Get comprehensive WebSocket connection information.
    
    Returns:
    - WebSocket endpoint details
    - Current number of active connections
    - Connection URL for clients
    - Connection status
    """
    return {
        "websocket_endpoint": "/ws/alerts",
        "active_connections": len(manager.active_connections),
        "connection_url": "ws://localhost:8000/ws/alerts",
        "status": "operational",
        "supported_events": {
            "incoming": ["ping", "message"],
            "outgoing": ["pong", "alert_notification"]
        }
    }