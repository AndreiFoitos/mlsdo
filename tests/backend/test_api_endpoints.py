import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.app import app

client = TestClient(app)

def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_hello_endpoint():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json()["message"] == "hello"

@patch("backend.api.app.get_db_connection")
def test_search_issues_mock_db(mock_db):
    # Mock DB connection and cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": 1, "summary": "Test", "description": "Desc", "label": "ADD", "created_at": "2026-01-21T00:00:00"}]
    mock_cursor.fetchone.side_effect = [{"total": 1}]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn

    response = client.get("/api/issues/search?keyword=Test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["label"] == "ADD"

@patch("backend.api.app.celery_app.send_task")
def test_predict_async_task(mock_send_task):
    mock_send_task.return_value.id = "fake-task-id"
    payload = {"summary": "Test summary", "description": "Test description"}
    response = client.post("/api/predictions", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "fake-task-id"
    assert data["status"] == "PENDING"

def test_submit_labeled_issue_invalid_label():
    payload = {"summary": "Test", "description": "Desc", "label": "INVALID"}
    response = client.post("/api/issues/labeled", json=payload)
    assert response.status_code == 400
    assert "Invalid label" in response.json()["detail"]
