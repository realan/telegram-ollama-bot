from __future__ import annotations

from app.utils.telegram_text import split_text


def test_split_text_keeps_short_message() -> None:
    assert split_text("short text", limit=20) == ["short text"]


def test_split_text_splits_by_words() -> None:
    text = "one two three four"

    assert split_text(text, limit=8) == ["one two", "three", "four"]


def test_split_text_falls_back_to_hard_split_for_long_tokens() -> None:
    text = "abcdefghij"

    assert split_text(text, limit=4) == ["abcd", "efgh", "ij"]

