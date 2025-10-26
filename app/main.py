from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
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


load_dotenv()

# --- MQTT Broker Configuration ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_ALERTS_TOPIC = os.getenv("MQTT_ALERTS_TOPIC", "obex/alerts")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# --- Initialize FastAPI App ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title="OBEX EDGE Backend API",
    description="API for the OBEX Vehicle Security System",
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

# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "OBEX Backend is running"}

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
    print(new_alert)
    return schema.Alert.from_orm(new_alert)

@app.get("/alerts", response_model=List[schema.Alert]) 
async def get_all_alerts(db: AsyncSession = Depends(get_db)):
    """Retrieve a list of all alerts."""
    result = await db.execute(select(models.Alert))
    alerts = result.scalars().all()
    return alerts