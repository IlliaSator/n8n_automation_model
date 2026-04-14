from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from news_trend_predictor.config.settings import Settings

LOGGER = logging.getLogger(__name__)


class NewsAPIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_raw_records(self) -> list[dict[str, Any]]:
        if not self.settings.news_api_base_url:
            LOGGER.info("NEWS_API_BASE_URL is not configured. Using sample payload from %s", self.settings.news_api_sample_path)
            return self._load_sample_payload()

        url = f"{self.settings.news_api_base_url.rstrip('/')}{self.settings.news_api_endpoint}"
        headers = {}
        if self.settings.news_api_key:
            headers["Authorization"] = f"Bearer {self.settings.news_api_key}"

        response = requests.get(url, headers=headers, timeout=self.settings.news_api_timeout_seconds)
        response.raise_for_status()
        data = response.json()

        records = self._extract_records(data)
        if not isinstance(records, list):
            raise ValueError("Configured records path does not point to a JSON list.")
        return records

    def _load_sample_payload(self) -> list[dict[str, Any]]:
        sample_path = Path(self.settings.news_api_sample_path)
        with sample_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        records = self._extract_records(data)
        if not isinstance(records, list):
            raise ValueError("Sample payload must contain a list of records.")
        return records

    def _extract_records(self, data: Any) -> Any:
        current = data
        for key in self.settings.news_api_records_path.split("."):
            if not key:
                continue
            if not isinstance(current, dict):
                raise ValueError("JSON records path points to a non-dict node.")
            current = current.get(key)
        return current
