import pytest
from unittest.mock import patch, MagicMock
from backend.inference.tasks import classify_issue

class DummyRequest:
    id = "task123"

@patch("backend.inference.tasks._mark_started")
@patch("backend.inference.tasks._mark_success")
@patch("backend.inference.tasks._mark_failure")
@patch("backend.inference.tasks.MLModelTask.model_and_tokenizer", new_callable=property)
def test_classify_issue_success(mock_model_tokenizer, mock_failure, mock_success, mock_started):
    # Mock model and tokenizer
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    mock_model_tokenizer.return_value = (mock_model, mock_tokenizer)

    # Mock model outputs
    mock_output = MagicMock()
    mock_output.logits = [[0.2, 0.8]]  # predicts class 1
    mock_model.__call__.return_value = mock_output

    # Call task
    task = classify_issue
    task.request = DummyRequest()
    result = task(task.request.id, "summary", "description")

    assert isinstance(result, dict)
    assert result["label"] == "ADD"
