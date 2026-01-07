"""WebSocket endpoint handlers."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import manager

router = APIRouter(
    tags=["WebSocket"]
)


@router.websocket("/ws/alerts/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time alert notifications.
    Handles client connections, disconnections, and keep-alive messages.
    """
    await manager.connect(websocket, user_id)
    print(f"New WebSocket connection established. Active connections: {len(manager.active_connections)}")
    
    try:
        await manager.send_connection_message(websocket)
        
        while True:
            await websocket.receive_text()
            await manager.send_pong(websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"WebSocket disconnected. Remaining connections: {len(manager.active_connections)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(user_id)
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
        "websocket_endpoint": "/ws/alerts/{user_id}",
        "active_connections": len(manager.active_connections),
        "connection_url": "ws://localhost:8000/ws/alerts/jnjznjianajajk-aasss-wssssa",
        "status": "operational",
        "supported_events": {
            "incoming": ["ping", "message"],
            "outgoing": ["pong", "alert_notification"]
        }
    }