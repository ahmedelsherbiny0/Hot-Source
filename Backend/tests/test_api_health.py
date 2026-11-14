"""
Basic API health tests for FastAPI entrypoint.
"""

from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Trend Detective API"
    assert "version" in data
    assert "endpoints" in data


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] in ("1.0.0", "1.1.0")
    assert "capabilities" in data
    assert len(data["capabilities"]) > 0
