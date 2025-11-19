"""
Tests for model log ingestion and dashboard summary endpoints.
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

def test_ingest_model_log(api_client: TestClient):
    payload = {
        "model_name": "test-model",
        "log_level": "INFO",
        "message": "Inference completed successfully.",
        "extra": {"duration": 0.23},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = api_client.post("/api/model-logs/", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["model_name"] == payload["model_name"]
    assert body["log_level"] == payload["log_level"]
    assert body["message"] == payload["message"]


def test_get_recent_model_logs(api_client: TestClient):
    response = api_client.get("/api/model-logs/recent?limit=5")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    if logs:
        assert "model_name" in logs[0]


def test_get_model_log_summary(api_client: TestClient):
    response = api_client.get("/api/model-logs/summary?since_hours=24")
    assert response.status_code == 200
    summary = response.json()
    assert "total_logs" in summary
    assert "error_logs" in summary
    assert "model_counts" in summary
