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

def test_metrics_endpoint_exposed():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")

def test_search_issues_empty_keyword_returns_400():
    resp = client.get("/api/issues/search?keyword=")
    assert resp.status_code == 400
    assert "Keyword parameter is required" in resp.json()["detail"]

@patch("backend.api.app.celery_app.send_task")
def test_predict_batch_async_returns_task_ids(mock_send_task):
    mock_send_task.side_effect = [MagicMock(id="id1"), MagicMock(id="id2")]

    payload = {
        "issues": [
            {"summary": "s1", "description": "d1"},
            {"summary": "s2", "description": "d2"},
        ]
    }
    resp = client.post("/api/predictions/batch", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["task_ids"] == ["id1", "id2"]
    assert mock_send_task.call_count == 2

@patch("backend.api.app.AsyncResult")
def test_get_prediction_status_pending(mock_async_result):
    mock_task = MagicMock()
    mock_task.status = "PENDING"
    mock_task.ready.return_value = False
    mock_async_result.return_value = mock_task

    resp = client.get("/api/predictions/fake-id")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "fake-id"
    assert data["status"] == "PENDING"
    assert "result" not in data
    assert "error" not in data

@patch("backend.api.app.AsyncResult")
def test_get_prediction_status_success(mock_async_result):
    mock_task = MagicMock()
    mock_task.status = "SUCCESS"
    mock_task.ready.return_value = True
    mock_task.successful.return_value = True
    mock_task.result = {"label": "ADD", "probability": 0.9}
    mock_async_result.return_value = mock_task

    resp = client.get("/api/predictions/fake-id")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["result"]["label"] == "ADD"

@patch("backend.api.app.AsyncResult")
def test_get_prediction_status_failure(mock_async_result):
    mock_task = MagicMock()
    mock_task.status = "FAILURE"
    mock_task.ready.return_value = True
    mock_task.successful.return_value = False
    mock_task.result = RuntimeError("boom")
    mock_async_result.return_value = mock_task

    resp = client.get("/api/predictions/fake-id")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "FAILURE"
    assert "boom" in data["error"]
