from __future__ import annotations

import json
from pathlib import Path

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.data_ingestion.client import NewsAPIClient
from news_trend_predictor.pipeline.orchestrator import PipelineRunner


def test_client_extracts_records_from_nested_payload() -> None:
    settings = Settings(news_api_records_path="data.items")
    client = NewsAPIClient(settings)

    payload = {"data": {"items": [{"id": "1"}, {"id": "2"}]}}
    records = client.extract_records(payload)

    assert isinstance(records, list)
    assert len(records) == 2


def test_pipeline_accepts_external_records_override(tmp_path) -> None:
    sample_payload = json.loads(Path("data/sample_news.json").read_text(encoding="utf-8"))
    records = sample_payload["articles"]

    settings = Settings(
        artifacts_dir=str(tmp_path / "artifacts"),
        enable_internal_google_sheets_logger=False,
        enable_internal_telegram_notifier=False,
    )
    result = PipelineRunner(settings).run(raw_records_override=records)

    assert result.status == "success"
    assert result.record_count == len(records)
