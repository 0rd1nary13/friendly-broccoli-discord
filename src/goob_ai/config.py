"""Configuration helpers for the relay app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

from dotenv import load_dotenv

DEFAULT_TRANSLATION_MODEL: Final[str] = "gemini-2.5-flash"
DEFAULT_TARGET_LANGUAGE: Final[str] = "English"
DEFAULT_SESSION_NAME: Final[str] = "telegram_relay_session"
DEFAULT_DISCORD_TIMEOUT_SECONDS: Final[float] = 12.0


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime configuration loaded from environment variables."""

    telegram_api_id: int
    telegram_api_hash: str
    telegram_session_name: str
    telegram_source_chats: list[str | int]
    gemini_api_key: str
    gemini_model: str
    target_language: str
    discord_webhook_url: str
    discord_timeout_seconds: float

    @classmethod
    def from_env(cls) -> AppConfig:
        """Build application config from environment variables."""
        load_dotenv()

        telegram_api_id_raw: str = _require_env("TELEGRAM_API_ID")
        try:
            telegram_api_id: int = int(telegram_api_id_raw)
        except ValueError as error:
            raise ConfigError("TELEGRAM_API_ID must be an integer.") from error

        source_chats_raw: str = _require_env("TELEGRAM_SOURCE_CHATS")
        source_chats: list[str | int] = _parse_source_chats(source_chats_raw)
        if not source_chats:
            raise ConfigError("TELEGRAM_SOURCE_CHATS cannot be empty.")

        discord_timeout_raw: str = os.getenv(
            "DISCORD_TIMEOUT_SECONDS", str(DEFAULT_DISCORD_TIMEOUT_SECONDS)
        )
        try:
            discord_timeout_seconds: float = float(discord_timeout_raw)
        except ValueError as error:
            raise ConfigError("DISCORD_TIMEOUT_SECONDS must be a number.") from error

        return cls(
            telegram_api_id=telegram_api_id,
            telegram_api_hash=_require_env("TELEGRAM_API_HASH"),
            telegram_session_name=os.getenv("TELEGRAM_SESSION_NAME", DEFAULT_SESSION_NAME),
            telegram_source_chats=source_chats,
            gemini_api_key=_require_env("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_TRANSLATION_MODEL),
            target_language=os.getenv("TARGET_LANGUAGE", DEFAULT_TARGET_LANGUAGE),
            discord_webhook_url=_require_env("DISCORD_WEBHOOK_URL"),
            discord_timeout_seconds=discord_timeout_seconds,
        )


def _require_env(name: str) -> str:
    """Read an environment variable and fail with a clear message when missing."""
    value: str | None = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigError(f"Missing required environment variable: {name}")
    return value.strip()


def _parse_source_chats(raw_value: str) -> list[str | int]:
    """Parse chat IDs/usernames from comma-separated env text."""
    chats: list[str | int] = []
    for item in raw_value.split(","):
        token: str = item.strip()
        if not token:
            continue
        if token.lstrip("-").isdigit():
            chats.append(int(token))
        else:
            chats.append(token)
    return chats
