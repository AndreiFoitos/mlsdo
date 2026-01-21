import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from backend.inference.tasks import classify_issue

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

    # When the model is called, return an object with logits
    mock_output = MagicMock()
    mock_output.logits = logits
    mock_model.return_value = mock_output

    # Patch property to return mock model and tokenizer
    mock_model_tokenizer.return_value = (mock_model, mock_tokenizer)

    # Call the task like a normal function
    task_id = "dummy-task-id"
    result = classify_issue(task_id, "summary text", "description text")

    # Assertions
    assert isinstance(result, dict)
    assert result["label"] == expected_label
    assert "probability" in result
    assert "types" in result
