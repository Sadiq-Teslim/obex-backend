from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from app import schema, models
import os
from contextlib import asynccontextmanager
from app.config.database import connect_db, close_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4
from datetime import datetime
import paho.mqtt.client as mqtt
import json
from dotenv import load_dotenv
import threading
import asyncio
from fastapi.responses import FileResponse

load_dotenv()

# --- MQTT Broker Configuration ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_ALERTS_TOPIC = os.getenv("MQTT_ALERTS_TOPIC", "obex/alerts")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)


# Initialize WebSocket manager
manager = ConnectionManager()

# --- Initialize FastAPI App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title="OBEX EDGE Backend API",
    description="API for the OBEX Vehicle Security System with WebSocket support",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# --- MQTT Client Logic ---
def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print(f"Connected to MQTT Broker at {MQTT_BROKER_HOST}")
        client.subscribe(MQTT_ALERTS_TOPIC)
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")
    
    try:
        payload = json.loads(msg.payload.decode())
        
        # Validate the data using Pydantic schema
        alert_data = schema.AlertCreate(**payload) 
        
        # Simulate adding to the database
        async def save_alert():
            async with AsyncSessionLocal() as session:
                new_alert = schema.Alert(**alert_data.dict())
                session.add(new_alert)
                await session.commit()
                print(f"✅ Stored alert in DB: {new_alert.alert_type}")

        import asyncio
        asyncio.create_task(save_alert())
    except json.JSONDecodeError:
        print("Error: Received message is not valid JSON.")
    except Exception as e:
        print(f"Error processing message: {e}")

# Create the MQTT client instance
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.tls_set()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.on_event("startup")
async def startup_event():
    def mqtt_thread():
        try:
            print("🔌 Connecting to MQTT broker...")
            mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")

    threading.Thread(target=mqtt_thread, daemon=True).start()

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from MQTT broker on app shutdown."""
    print("Disconnecting from MQTT broker...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

# --- WebSocket Endpoint ---
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # This Keep connection alive, wait for any data (can be used for ping/pong)
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(json.dumps({"type": "pong", "message": "Connection active"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- API Endpoints ---

@app.get("/home")
async def serve_homepage():
    """Serve the HTML test page"""
    return FileResponse("index.html")

@app.get("/index.html")
async def serve_index():
    """Alternative endpoint for the HTML page"""
    return FileResponse("index.html")

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {
        "status": "OBEX Backend is running", 
        "websocket_url": "ws://localhost:8000/ws/alerts",
        "active_websocket_connections": len(manager.active_connections),
        "websocket_info_endpoint": "/websocket-info"
    }

@app.post("/devices/register", response_model=schema.Device) 
async def register_device(device: schema.DeviceCreate, db: AsyncSession = Depends(get_db)): 
    """Register a new edge device (e.g., Raspberry Pi) with the system."""
    new_device = models.Device(**device.dict(), id=uuid4(), created_at=datetime.utcnow())
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device

@app.post("/alerts", response_model=schema.Alert) 
async def receive_alert(alert: schema.AlertCreate, db: AsyncSession = Depends(get_db)): 
    """
    (This endpoint is still useful for testing with HTTP)
    Receives a new alert from an edge device.
    """
    new_alert = models.Alert(**alert.dict(), id=uuid4())
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
    
    # Broadcast via WebSocket
    alert_response = schema.Alert.from_orm(new_alert)
    broadcast_message = json.dumps({
        "type": "new_alert", 
        "alert": json.loads(alert_response.json()),
        "timestamp": datetime.utcnow().isoformat()
    })
    await manager.broadcast(broadcast_message)
    
    print(f" HTTP Alert stored and broadcasted to {len(manager.active_connections)} clients")
    return alert_response

@app.get("/alerts", response_model=List[schema.Alert]) 
async def get_all_alerts(db: AsyncSession = Depends(get_db)):
    """Retrieve a list of all alerts."""
    result = await db.execute(select(models.Alert))
    alerts = result.scalars().all()
    return alerts

    

@app.get("/websocket-info")
async def get_websocket_info():
    """Get WebSocket connection information."""
    return {
        "websocket_endpoint": "/ws/alerts",
        "active_connections": len(manager.active_connections),
        "connection_url": "ws://localhost:8000/ws/alerts"
    }

