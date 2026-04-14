from news_trend_predictor.preprocessing.text import clean_text


def test_clean_text_removes_noise_and_lowercases() -> None:
    assert clean_text(" Hello, WORLD!!! 42\n") == "hello world 42"


def test_clean_text_handles_empty_values() -> None:
    assert clean_text(None) == ""
