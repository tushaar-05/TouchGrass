"""Tests for API health and system information endpoint."""
from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Sit Spot"
    assert "platform" in data
    assert "limits" in data
    assert data["limits"]["max_duration_seconds"] == 300.0
    assert data["limits"]["max_file_size_bytes"] == 25 * 1024 * 1024
    assert data["local_model"]["configured_model"] == "Google YAMNet (ONNX)"
    assert data["local_model"]["license"] == "Apache-2.0"
