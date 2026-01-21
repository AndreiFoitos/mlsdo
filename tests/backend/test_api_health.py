from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_root_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data
