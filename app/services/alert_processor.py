"""Core alert processing and storage functionality."""

import json
from uuid import uuid4
from fastapi import HTTPException

from app.db.session import AsyncSessionLocal
from app.models import Alert
from app.schemas.alerts import AlertCreate, Alert as AlertSchema
from app.services import auth_service
from app.services.websocket import manager
from app.utils.termii import send_sms
from app.utils.email import send_email


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
            print(alert_data)
            alert_dict = alert_data.model_dump()
            print(f"Processing alert data from {source}: {alert_dict}")
            
            alert_id = uuid4()
            
            new_alert = Alert(
                **alert_dict,
                id=alert_id
            )
            
            session.add(new_alert)
            try:
                await session.commit()
                await session.refresh(new_alert)
            except Exception as db_error:
                print(f"Database error: {db_error}")
                await session.rollback()
                raise db_error
            
            print(f"Alert from {source} saved successfully: {new_alert.alert_type}")

            try:
                alert_response = AlertSchema.from_orm(new_alert)
            except Exception as schema_error:
                print(f"Schema conversion error: {schema_error}")
                raise schema_error
            
            try:
                alert_dict = alert_response.model_dump(mode="json")
                broadcast_message = json.dumps({
                    "type": "new_alert",
                    "alert": {
                        "id": alert_dict["id"],
                        "user_id": alert_dict["user_id"],
                        "device_id": alert_dict["device_id"],
                        "timestamp": alert_dict["timestamp"],
                        "alert_type": alert_dict["alert_type"],
                        "location_lat": alert_dict["location_lat"],
                        "location_lon": alert_dict["location_lon"],
                        "payload": alert_dict["payload"]
                    }
                })
                print("Broadcasting alert to connected clients")
                
                await manager.broadcast(broadcast_message, user_id=alert_response.user_id)
            except Exception as broadcast_error:
                print(f"WebSocket broadcast error: {broadcast_error}")

            try:
                notification_message = (
                    f"Alert Type: {alert_response.alert_type}\n"
                    f"User ID: {alert_response.user_id}\n"
                    f"Device ID: {alert_response.device_id}\n"
                    f"Timestamp: {alert_response.timestamp}\n"
                    f"Location: ({alert_response.location_lat}, {alert_response.location_lon})\n"
                    f"Payload: {alert_response.payload}\n"
                )
                
                user = await auth_service.get_user_by_id(alert_response.user_id)
                
                # sent_sms = await send_sms(
                #     phone_number=user.phone_number if user else None,
                #     message=notification_message
                # )

                # if sent_sms:
                #     print(f"Notification SMS sent to {user.phone_number if user else 'unknown user'}")
                # else:
                #     print("Failed to send notification SMS")

                sent_email = send_email(
                    to=user.email if user else None,
                    subject="New Obex Security Alert Received",
                    body=notification_message
                )
                if sent_email:
                    print(f"Notification email sent to {user.email if user else 'unknown user'}")
                else:
                    print("Failed to send notification email")
            except Exception as notification_error:
                print(f"Notification error: {notification_error}")
            
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