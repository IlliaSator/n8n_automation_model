from __future__ import annotations

import logging

import requests

from news_trend_predictor.config.settings import Settings

LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: str) -> None:
        if not self.settings.enable_internal_telegram_notifier:
            LOGGER.info("Internal Telegram notifier is disabled. Skipping notification.")
            return

        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            LOGGER.info("Telegram is not configured. Skipping notification.")
            return

        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": self.settings.telegram_chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
