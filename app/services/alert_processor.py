"""Core alert processing and storage functionality."""

import json
from uuid import uuid4
from fastapi import HTTPException

from app.db.session import AsyncSessionLocal
from app.models import Alert
from app.schemas.alerts import AlertCreate, Alert as AlertSchema
from app.services.websocket import manager


async def process_and_save_alert(alert_data: AlertCreate, source: str):
    """
    Saves a validated alert to the DB and broadcasts it.
    This is the single source of truth for creating alerts.
    
    Args:
        alert_data: Validated alert data
        source: Origin of the alert ("MQTT" or "HTTP")
        
    Returns:
        AlertSchema: The processed and saved alert
        
    Raises:
        HTTPException: If there's an error processing the alert
    """
    async with AsyncSessionLocal() as session:
        try:
            # Convert Pydantic model to dict
            alert_dict = alert_data.model_dump()
            print(f"Processing alert data from {source}: {alert_dict}")
            
            # Generate UUID and convert to string for SQLite compatibility
            alert_id = str(uuid4())
            
            # Create SQLAlchemy model instance
            new_alert = Alert(
                **alert_dict,
                id=alert_id
            )
            
            # Persist to database
            session.add(new_alert)
            try:
                await session.commit()
                await session.refresh(new_alert)
            except Exception as db_error:
                print(f"Database error: {db_error}")
                await session.rollback()
                raise db_error
            
            print(f"Alert from {source} saved successfully: {new_alert.alert_type}")

            # Create Pydantic model for broadcast
            try:
                alert_response = AlertSchema.from_orm(new_alert)
            except Exception as schema_error:
                print(f"Schema conversion error: {schema_error}")
                raise schema_error
            
            # Broadcast to WebSocket clients
            try:
                alert_dict = alert_response.model_dump(mode="json")
                broadcast_message = json.dumps({
                    "type": "new_alert",
                    "alert": {
                        "id": alert_dict["id"],
                        "device_id": alert_dict["device_id"],
                        "timestamp": alert_dict["timestamp"],
                        "alert_type": alert_dict["alert_type"],
                        "location_lat": alert_dict["location_lat"],
                        "location_lon": alert_dict["location_lon"],
                        "payload": alert_dict["payload"]
                    }
                })
                print(f"Broadcasting alert to connected clients")
                await manager.broadcast(broadcast_message)
            except Exception as broadcast_error:
                print(f"WebSocket broadcast error: {broadcast_error}")
            
            return alert_response

        except Exception as e:
            await session.rollback()
            print(f"Error saving alert from {source}: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing alert: {str(e)}"
            )