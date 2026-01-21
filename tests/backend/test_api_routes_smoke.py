from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_hello_endpoint():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json()["message"] == "hello"


def test_prediction_endpoint_validation():
    # Missing fields should fail
    response = client.post("/api/predictions", json={})
    assert response.status_code == 422
