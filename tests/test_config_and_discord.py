"""Tests for configuration parsing and Discord message splitting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from goob_ai.config import _parse_source_chats
from goob_ai.discord_sender import split_for_discord
from goob_ai.translator import TranslationService, _contains_chinese_text

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

    _TYPE_CHECKING_IMPORTS = (
        CaptureFixture,
        FixtureRequest,
        LogCaptureFixture,
        MonkeyPatch,
        MockerFixture,
    )


def test_parse_source_chats_mixed_values() -> None:
    """Parses numeric IDs and usernames from comma-separated values."""
    parsed: list[str | int] = _parse_source_chats("12345, -1001234567890, my_channel")
    assert parsed == [12345, -1001234567890, "my_channel"]


def test_split_for_discord_keeps_text_integrity() -> None:
    """Splits long content into bounded chunks without changing payload."""
    message: str = "A" * 2500
    chunks: list[str] = split_for_discord(message, limit=1000)
    assert len(chunks) == 3
    assert "".join(chunks) == message
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_contains_chinese_text_detects_cjk() -> None:
    """Detects whether incoming text contains Chinese characters."""
    assert _contains_chinese_text("这是中文")
    assert not _contains_chinese_text("Only English text")


def test_build_prompt_requests_clean_english_article_body() -> None:
    """Builds prompt that asks for English body-only translation output."""
    service: TranslationService = TranslationService(
        api_key="test-key",
        model="gemini-2.5-flash",
        target_language="English",
    )
    prompt: str = service._build_prompt("测试内容\n作者：张三")

    assert "Translate the following Chinese text into English" in prompt
    assert "Remove signatures, bylines, hashtags, source credits" in prompt
    assert "Return only the translated article body" in prompt
