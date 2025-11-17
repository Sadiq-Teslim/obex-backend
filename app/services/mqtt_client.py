"""MQTT client and message handling functionality."""

import json
import asyncio
import paho.mqtt.client as mqtt
from app.core.settings import MQTT_CONFIG
from app.schemas.alerts import AlertCreate
from concurrent.futures import ThreadPoolExecutor
from app.services.alert_processor import process_and_save_alert


class MQTTService:
    """MQTT client service for handling alert messages."""
    
    def __init__(self):
        self.client = mqtt.Client()
        if MQTT_CONFIG["USERNAME"] and MQTT_CONFIG["PASSWORD"]:
            self.client.username_pw_set(MQTT_CONFIG["USERNAME"], MQTT_CONFIG["PASSWORD"])
            # Check if host is HiveMQ to enable TLS
            if "hivemq.cloud" in MQTT_CONFIG["BROKER_HOST"]:
                print("Enabling TLS for HiveMQ MQTT.")
                self.client.tls_set()
                
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.running = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT broker connection."""
        if rc == 0:
            print(f"Successfully connected to MQTT Broker at {MQTT_CONFIG['BROKER_HOST']}")
            client.subscribe(MQTT_CONFIG["ALERTS_TOPIC"])
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for MQTT message reception."""
        print(f"Received message on topic {msg.topic}")
        
        try:
            # Parse and validate the message
            payload = json.loads(msg.payload.decode())
            print(payload)
            alert_data = AlertCreate(**payload)
            
            # Process alert in a new event loop for thread safety
            asyncio.run_coroutine_threadsafe(process_and_save_alert(alert_data, source="MQTT"), self.loop)
            
        except json.JSONDecodeError:
            print("Error: Received MQTT message is not valid JSON")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def start(self):
        """Initialize and start the MQTT client loop."""
        self.running = True
        try:
            print("Initializing MQTT connection...")
            self.client.connect(MQTT_CONFIG["BROKER_HOST"], MQTT_CONFIG["BROKER_PORT"], 60)
            self.client.loop_forever()  # Blocking call that processes network traffic
        except Exception as e:
            print(f"Critical MQTT connection failure: {e}")
    
    def stop(self):
        """Disconnect the MQTT client."""
        self.running = True
        print("Disconnecting from MQTT broker...")
        self.client.disconnect()

# Create global instance for app-wide use
mqtt_service = MQTTService()