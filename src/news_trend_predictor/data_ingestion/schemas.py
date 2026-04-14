from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dateutil import parser as date_parser


@dataclass(slots=True)
class NewsFieldMapping:
    id_field: str
    title_field: str
    text_field: str
    summary_field: str
    published_at_field: str
    source_field: str
    category_field: str
    url_field: str


@dataclass(slots=True)
class NewsRecord:
    record_id: str
    title: str
    text: str
    published_at: datetime
    source: str
    category: str
    url: str
    raw_payload: dict[str, Any]


class NewsResponseParser:
    def __init__(self, field_mapping: NewsFieldMapping) -> None:
        self.field_mapping = field_mapping

    def parse_records(self, payload: list[dict[str, Any]]) -> list[NewsRecord]:
        return [self.parse_record(item) for item in payload]

    def parse_record(self, item: dict[str, Any]) -> NewsRecord:
        mapping = self.field_mapping
        published_raw = item.get(mapping.published_at_field)
        if not published_raw:
            raise ValueError("Field 'published_at' is required for time-based training.")

        title = self._get_str(item, mapping.title_field)
        text = self._get_str(item, mapping.text_field) or self._get_str(item, mapping.summary_field)
        record_id = self._get_str(item, mapping.id_field) or self._build_fallback_id(title, published_raw)

        return NewsRecord(
            record_id=record_id,
            title=title,
            text=text,
            published_at=date_parser.parse(str(published_raw)),
            source=self._get_str(item, mapping.source_field) or "unknown",
            category=self._get_str(item, mapping.category_field) or "unknown",
            url=self._get_str(item, mapping.url_field),
            raw_payload=item,
        )

    @staticmethod
    def _get_str(item: dict[str, Any], key: str) -> str:
        value = item.get(key)
        return "" if value is None else str(value).strip()

    @staticmethod
    def _build_fallback_id(title: str, published_at: str) -> str:
        safe_title = title.lower().replace(" ", "-")[:40]
        return f"{safe_title or 'news'}-{published_at}"
