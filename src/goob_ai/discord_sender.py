"""Discord webhook sender."""

from __future__ import annotations

import logging
from typing import Final

import requests
from requests import Response
from requests.exceptions import RequestException

DISCORD_MESSAGE_LIMIT: Final[int] = 2000


class DiscordSender:
    """Post relay messages to a Discord webhook."""

    def __init__(self, webhook_url: str, timeout_seconds: float) -> None:
        """Store delivery settings for outgoing webhook calls."""
        self._webhook_url: str = webhook_url
        self._timeout_seconds: float = timeout_seconds
        self._logger: logging.Logger = logging.getLogger(__name__)

    def send(self, text: str) -> None:
        """Send text and split it into multiple webhook posts when necessary."""
        for chunk in split_for_discord(text):
            self._post_chunk(chunk)

    def _post_chunk(self, content: str) -> None:
        """Send one chunk to Discord and raise on delivery errors."""
        try:
            response: Response = requests.post(
                self._webhook_url,
                json={"content": content},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as error:
            self._logger.exception("Failed to send message to Discord webhook.")
            raise RuntimeError("Discord webhook delivery failed.") from error


def split_for_discord(message: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    """Split a message into Discord-safe chunks without dropping content."""
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    current_lines: list[str] = []
    current_length: int = 0

    for line in message.splitlines(keepends=True):
        line_length: int = len(line)
        if line_length > limit:
            if current_lines:
                chunks.append("".join(current_lines))
                current_lines = []
                current_length = 0
            chunks.extend(_split_long_token(line, limit))
            continue

        if current_length + line_length > limit:
            chunks.append("".join(current_lines))
            current_lines = [line]
            current_length = line_length
            continue

        current_lines.append(line)
        current_length += line_length

    if current_lines:
        chunks.append("".join(current_lines))
    return chunks


def _split_long_token(token: str, limit: int) -> list[str]:
    """Split a long string into exact-length slices."""
    return [token[index : index + limit] for index in range(0, len(token), limit)]
