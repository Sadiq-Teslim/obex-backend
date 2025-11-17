"""Tests for alert ingestion and retrieval flows."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.schemas.alerts import AlertCreate
from app.services.alert_processor import process_and_save_alert
from app.services.alert_query import AlertQueryService
from app.services.websocket import manager


def _example_alert_payload(timestamp: datetime) -> dict:
    return {
        "device_id": "device-123",
        "timestamp": timestamp.isoformat(),
        "alert_type": "weapon_detection",
        "location_lat": 6.5244,
        "location_lon": 3.3792,
        "payload": {"confidence": 0.92},
    }


@pytest.mark.asyncio
async def test_process_and_save_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Saving an alert should persist it and broadcast to clients."""

    broadcast_messages = []

    async def fake_broadcast(message: str) -> None:
        broadcast_messages.append(message)

    monkeypatch.setattr(manager, "broadcast", fake_broadcast)

    alert_data = AlertCreate(**_example_alert_payload(datetime.utcnow()))
    result = await process_and_save_alert(alert_data, source="HTTP")

    assert result.device_id == alert_data.device_id
    assert result.alert_type == alert_data.alert_type
    assert broadcast_messages, "Expected broadcast to be triggered"

    now = datetime.utcnow()
    alerts = await AlertQueryService.get_alerts_by_timeframe(
        start_time=now - timedelta(minutes=1),
        end_time=now + timedelta(minutes=1),
    )
    assert len(alerts) == 1


def test_receive_alert_endpoint(api_client: TestClient) -> None:
    """Posting to the alert endpoint should persist and return the alert."""

    payload = _example_alert_payload(datetime.utcnow())
    response = api_client.post("/api/alerts", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["device_id"] == payload["device_id"]

    list_response = api_client.get("/api/alerts")
    assert list_response.status_code == 200
    alerts = list_response.json()
    assert len(alerts) == 1
    assert alerts[0]["device_id"] == payload["device_id"]


def test_invalid_alert_payload_returns_422(api_client: TestClient) -> None:
    """Validation errors bubble up as 422 responses."""

    invalid_payload = {"device_id": "test", "timestamp": "nope", "alert_type": "unknown"}
    response = api_client.post("/api/alerts", json=invalid_payload)
    assert response.status_code == 422