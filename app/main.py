from fastapi import FastAPI, HTTPException
from typing import List
from app import schema 
from datetime import datetime
import paho.mqtt.client as mqtt
import json

# --- MQTT Broker Configuration ---
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_ALERTS_TOPIC = "obex/alerts" 

# --- Initialize FastAPI App ---
app = FastAPI(
    title="OBEX Backend API",
    description="API for the OBEX Vehicle Security System",
    version="0.1.0"
)

# --- In-Memory "Database" ---
db_devices: List[schema.Device] = [] 
db_alerts: List[schema.Alert] = [] 

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
        new_alert = schema.Alert( 
            **alert_data.dict(),
            id=len(db_alerts) + 1
        )
        db_alerts.append(new_alert)
        
        print(f"Successfully processed and stored alert: {new_alert.alert_type}")
        
    except json.JSONDecodeError:
        print("Error: Received message is not valid JSON.")
    except Exception as e:
        print(f"Error processing message: {e}")

# Create the MQTT client instance
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.on_event("startup")
async def startup_event():
    """Connect to MQTT broker on app startup."""
    print("Attempting to connect to MQTT broker...")
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()

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
def register_device(device: schema.DeviceCreate): 
    """Register a new edge device (e.g., Raspberry Pi) with the system."""
    new_device = schema.Device( 
        **device.dict(),
        id=len(db_devices) + 1,
        created_at=datetime.utcnow()
    )
    db_devices.append(new_device)
    return new_device

@app.post("/alerts", response_model=schema.Alert) 
def receive_alert(alert: schema.AlertCreate): 
    """
    (This endpoint is still useful for testing with HTTP)
    Receives a new alert from an edge device.
    """
    new_alert = schema.Alert( 
        **alert.dict(),
        id=len(db_alerts) + 1
    )
    db_alerts.append(new_alert)
    print(f"New Alert Received (via HTTP): {new_alert.alert_type}")
    return new_alert

@app.get("/alerts", response_model=List[schema.Alert]) 
def get_all_alerts():
    """Retrieve a list of all alerts."""
    return db_alerts