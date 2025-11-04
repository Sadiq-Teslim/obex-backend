"""Alert endpoint handlers."""

from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select

from app.models import Alert
from app.schemas.alerts import AlertCreate, Alert as AlertSchema
from app.services.alert_processor import process_and_save_alert
from app.db.session import get_db_session

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"]
)


@router.post(
    "",
    response_model=AlertSchema,
    summary="Create a new alert",
    status_code=201,
    description="""Submit a new security alert. The alert will be saved to the database
    and broadcast to all connected WebSocket clients.
    
    Alerts can be submitted via this HTTP endpoint or through the MQTT topic: `obex/alerts`"""
)
async def receive_alert(alert_data: AlertCreate):
    """
    Create and broadcast a new security alert.
    
    - **device_id**: ID of the device that detected the alert
    - **timestamp**: When the alert occurred (ISO 8601 format)
    - **alert_type**: Type of security event detected
    - **location_lat**: Optional latitude coordinate
    - **location_lon**: Optional longitude coordinate
    - **payload**: Optional additional data (e.g., confidence score, bounding box)
    
    The ID field is auto-generated and should NOT be included in the request.
    """
    alert_response = await process_and_save_alert(alert_data, source="HTTP")
    if alert_response:
        return alert_response
    else:
        raise HTTPException(status_code=500, detail="Error processing alert")


@router.get(
    "",
    response_model=List[AlertSchema],
    summary="Get all alerts",
    description="Retrieve all security alerts from the database, ordered by timestamp (newest first)."
)
async def get_all_alerts(db=get_db_session):
    """
    Retrieve a list of all alerts from the database.
    
    The alerts are sorted by timestamp in descending order (newest first).
    For real-time notifications, connect to the WebSocket endpoint: `/ws/alerts`
    """
    async with db as session:
        result = await session.execute(select(Alert).order_by(Alert.timestamp.desc()))
        alerts = result.scalars().all()
        return alerts