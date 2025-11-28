import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_signup_and_login_flow(api_client: TestClient):
    payload = {
        "username": "testuser",
        "password": "StrongPass1",
        "ipAddress": "127.0.0.1",
        "path": "/api/auth/signup",
        "port": 8000
    }
    # signup
    r = api_client.post("/api/auth/signup", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "testuser"

    # login
    login_payload = {"username": "testuser", "password": "StrongPass1"}
    r2 = api_client.post("/api/auth/login", json=login_payload)
    assert r2.status_code == 200
    b2 = r2.json()
    assert "access_token" in b2
    assert "refresh_token" in b2


def test_lockout_after_failed_attempts(api_client: TestClient):
    username = "lockout-user"
    # create user
    payload = {"username": username, "password": "LockPass1"}
    r = api_client.post("/api/auth/signup", json=payload)
    assert r.status_code == 201

    # fail login 6 times
    for i in range(6):
        r2 = api_client.post("/api/auth/login", json={"username": username, "password": "wrongpass"})
        # after several attempts should be unauthorized
        assert r2.status_code in (401, 400)

    # correct password should now be rejected due to lockout
    r3 = api_client.post("/api/auth/login", json={"username": username, "password": "LockPass1"})
    assert r3.status_code == 401
