"""Entrypoint for Telegram to Discord relay."""

from __future__ import annotations

import asyncio
import logging

from goob_ai.config import AppConfig, ConfigError
from goob_ai.discord_sender import DiscordSender
from goob_ai.telegram_listener import TelegramRelay
from goob_ai.translator import TranslationService


def configure_logging() -> None:
    """Configure global logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run() -> None:
    """Load config and run relay service."""
    configure_logging()
    try:
        config: AppConfig = AppConfig.from_env()
    except ConfigError as error:
        logging.getLogger(__name__).error("Invalid configuration: %s", error)
        raise

    translator: TranslationService = TranslationService(
        api_key=config.gemini_api_key,
        model=config.gemini_model,
        target_language=config.target_language,
    )
    discord_sender: DiscordSender = DiscordSender(
        webhook_url=config.discord_webhook_url,
        timeout_seconds=config.discord_timeout_seconds,
    )
    relay: TelegramRelay = TelegramRelay(config, translator, discord_sender)
    await relay.start()


def main() -> int:
    """Run async app and convert known startup failures to exit codes."""
    try:
        asyncio.run(run())
    except ConfigError:
        return 2
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutdown requested by keyboard interrupt.")
        return 0
    except Exception:
        logging.getLogger(__name__).exception("Unhandled fatal error.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
