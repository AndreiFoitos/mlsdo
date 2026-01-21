from backend.inference.tasks import clean_text

def test_clean_text_removes_html():
    text = "<b>Hello</b>   world"
    cleaned = clean_text(text)
    assert cleaned == "Hello world"


def test_clean_text_handles_none():
    assert clean_text(None) == ""
