import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from backend.inference.tasks import classify_issue

class DummyRequest:
    id = "task123"

@pytest.mark.parametrize("logits,expected_label", [
    ([[0.2, 0.8]], "ADD"),
    ([[0.7, 0.3]], "NON-ADD"),
])
@patch("backend.inference.tasks._mark_started")
@patch("backend.inference.tasks._mark_success")
@patch("backend.inference.tasks._mark_failure")
@patch("backend.inference.tasks.MLModelTask.model_and_tokenizer", new_callable=PropertyMock)
def test_classify_issue_prediction(mock_model_tokenizer, mock_failure, mock_success, mock_started, logits, expected_label):
    # Mock model and tokenizer
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    mock_model_tokenizer.return_value = (mock_model, mock_tokenizer)

    # Mock model outputs
    mock_output = MagicMock()
    mock_output.logits = logits
    mock_model.__call__.return_value = mock_output

    # Call task
    task = classify_issue
    task.request = DummyRequest()
    result = task(task.request.id, "summary", "description")

    assert isinstance(result, dict)
    assert result["label"] == expected_label
