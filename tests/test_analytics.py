"""Analytics endpoint tests."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def _create_sample_alert(client: TestClient, **overrides) -> None:
    payload = {
        "device_id": "analytics-device",
        "timestamp": datetime.utcnow().isoformat(),
        "alert_type": "weapon_detection",
        "location_lat": 6.5,
        "location_lon": 3.3,
        "payload": {"confidence": 0.9},
    }
    payload.update(overrides)
    response = client.post("/api/alerts", json=payload)
    assert response.status_code == 201


def test_timeframe_endpoint(api_client: TestClient) -> None:
    now = datetime.utcnow()
    _create_sample_alert(api_client, timestamp=(now - timedelta(minutes=10)).isoformat())

    response = api_client.get(
        "/api/analytics/alerts/timeframe",
        params={
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": now.isoformat(),
        },
    )
    assert response.status_code == 200
    assert response.json()


def test_location_endpoint(api_client: TestClient) -> None:
    _create_sample_alert(api_client)

    response = api_client.get(
        "/api/analytics/alerts/location",
        params={"lat": 6.5, "lon": 3.3, "radius_km": 1.0},
    )
    assert response.status_code == 200
    assert response.json()

    invalid = api_client.get(
        "/api/analytics/alerts/location",
        params={"lat": 91, "lon": 3.3, "radius_km": 1.0},
    )
    assert invalid.status_code == 422


def test_counts_endpoint(api_client: TestClient) -> None:
    now = datetime.utcnow()
    _create_sample_alert(api_client, timestamp=(now - timedelta(minutes=5)).isoformat())

    response = api_client.get("/api/analytics/alerts/counts")
    assert response.status_code == 200
    assert response.json()


def test_trends_endpoint(api_client: TestClient) -> None:
    _create_sample_alert(api_client)

    response = api_client.get("/api/analytics/alerts/trends", params={"days": 1, "interval_hours": 1})
    assert response.status_code == 200
    assert response.json()


def test_device_statistics_endpoint(api_client: TestClient) -> None:
    _create_sample_alert(api_client)

    response = api_client.get("/api/analytics/devices/analytics-device/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_alerts"] == 1


def test_error_responses(api_client: TestClient) -> None:
    response = api_client.get("/api/analytics/alerts/location")
    assert response.status_code == 422

    response = api_client.get("/api/analytics/alerts/trends", params={"days": "invalid"})
    assert response.status_code == 422

    response = api_client.get(
        "/api/analytics/alerts/timeframe",
        params={"start_time": "bad", "end_time": "also-bad"},
    )
    assert response.status_code == 422