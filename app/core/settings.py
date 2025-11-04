"""Application settings and configuration."""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# MQTT Configuration
MQTT_CONFIG = {
    "BROKER_HOST": os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org"),
    "BROKER_PORT": int(os.getenv("MQTT_BROKER_PORT", 1883)),
    "ALERTS_TOPIC": os.getenv("MQTT_ALERTS_TOPIC", "obex/alerts"),
    "USERNAME": os.getenv("MQTT_USERNAME", ""),
    "PASSWORD": os.getenv("MQTT_PASSWORD", ""),
    "USE_TLS": os.getenv("MQTT_USE_TLS", "false").lower() in ("1", "true", "yes")
}

# API Configuration
API_CONFIG = {
    "TITLE": "OBEX EDGE Backend API",
    "DESCRIPTION": """
    ## OBEX Vehicle Security System API
    
    Real-time security alert processing with MQTT and WebSocket support.
    
    ### Features:
    * Real-time alert creation and retrieval
    * Device registration and management
    * WebSocket live streaming of alerts
    * MQTT broker integration for edge devices
    
    ### Test Points:
    1. **Device Registration**: Register a new device with `/api/devices/register`
    2. **Alert Creation**: Send alerts via `/api/alerts` or MQTT
    3. **WebSocket**: Connect to `/ws/alerts` for real-time updates
    4. **Alert Retrieval**: List alerts with GET `/api/alerts`
    
    ### Important Notes:
    * **IDs are auto-generated** - Do NOT include `id` field when creating devices or alerts
    * All timestamps use ISO 8601 format (e.g., "2025-11-04T00:00:00Z")
    * WebSocket endpoint: `ws://localhost:8000/ws/alerts`
    * MQTT topic: `obex/alerts`
    
    ### Alert Types:
    - weapon_detection
    - unauthorized_passenger
    - aggression_detection
    - harassment_detection
    - robbery_pattern
    - route_deviation
    - driver_fatigue
    - distress_detection
    """,
    "VERSION": "0.2.0",
    "CONTACT": {
        "name": "OBEX Team",
        "url": "https://github.com/Sadiq-Teslim/obex-backend",
    },
    "LICENSE": {
        "name": "MIT",
    }
}