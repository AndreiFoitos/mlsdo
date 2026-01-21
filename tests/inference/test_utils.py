import pytest
from backend.inference.tasks import clean_text, _get_tracking_uri

def test_clean_text_removes_html():
    assert clean_text("<b>Hello</b>  world") == "Hello world"

def test_clean_text_none_returns_empty():
    assert clean_text(None) == ""

def test_get_tracking_uri_returns_env(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    assert _get_tracking_uri() == "http://localhost:5000"
