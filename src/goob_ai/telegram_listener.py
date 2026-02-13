"""Telegram event listener and relay orchestration."""

from __future__ import annotations

import logging

from telethon import TelegramClient, events
from telethon.events import NewMessage

from goob_ai.config import AppConfig
from goob_ai.discord_sender import DiscordSender
from goob_ai.translator import TranslationService


class TelegramRelay:
    """Coordinate Telegram input, AI translation, and Discord output."""

    def __init__(
        self,
        config: AppConfig,
        translator: TranslationService,
        discord_sender: DiscordSender,
    ) -> None:
        """Initialize relay dependencies and Telegram client."""
        self._config: AppConfig = config
        self._translator: TranslationService = translator
        self._discord_sender: DiscordSender = discord_sender
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._client: TelegramClient = TelegramClient(
            config.telegram_session_name,
            config.telegram_api_id,
            config.telegram_api_hash,
        )

        self._client.add_event_handler(
            self._handle_message,
            events.NewMessage(chats=config.telegram_source_chats),
        )

    async def start(self) -> None:
        """Start listening and keep process alive until disconnected."""
        await self._client.start()
        self._logger.info(
            "Relay started. Listening chats=%s model=%s target_language=%s",
            self._config.telegram_source_chats,
            self._config.gemini_model,
            self._config.target_language,
        )
        await self._client.run_until_disconnected()

    async def _handle_message(self, event: NewMessage.Event) -> None:
        """Process one Telegram message event and forward translated content."""
        source_text: str = event.message.message or ""
        if not source_text.strip():
            self._logger.debug("Skip empty message. chat_id=%s", event.chat_id)
            return

        self._logger.info("Received message. chat_id=%s", event.chat_id)
        try:
            translated_text: str = await self._translator.translate(source_text)
            if not translated_text:
                self._logger.warning(
                    "Translation returned empty content. chat_id=%s", event.chat_id
                )
                return
            self._discord_sender.send(translated_text)
            self._logger.info("Forwarded translated message to Discord. chat_id=%s", event.chat_id)
        except Exception:
            self._logger.exception("Failed processing incoming message. chat_id=%s", event.chat_id)
