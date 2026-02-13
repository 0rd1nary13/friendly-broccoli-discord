"""Tests for configuration parsing and Discord message splitting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from goob_ai.config import _parse_source_chats
from goob_ai.discord_sender import split_for_discord

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
