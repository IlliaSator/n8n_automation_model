from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from news_trend_predictor.config.settings import get_settings
from news_trend_predictor.data_ingestion.schemas import NewsFieldMapping, NewsResponseParser
from news_trend_predictor.features.builder import FeatureBuilder
from news_trend_predictor.model_registry.local import LocalModelRegistry


def extract_records(payload: object, records_path: str) -> list[dict]:
    if isinstance(payload, list):
        return payload

    current = payload
    for key in records_path.split("."):
        if not key:
            continue
        if not isinstance(current, dict):
            raise ValueError("Configured records path does not point to a list.")
        current = current[key]

    if not isinstance(current, list):
        raise ValueError("Configured records path does not resolve to a list.")
    return current


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference for a JSON file with news records.")
    parser.add_argument("--input", required=True, help="Path to input JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    registry = LocalModelRegistry(settings)
    bundle = registry.load_active_model()
    if bundle is None:
        raise FileNotFoundError("Active model not found. Train the pipeline first.")

    raw_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    parser = NewsResponseParser(
        NewsFieldMapping(
            id_field=settings.field_id,
            title_field=settings.field_title,
            text_field=settings.field_text,
            summary_field=settings.field_summary,
            published_at_field=settings.field_published_at,
            source_field=settings.field_source,
            category_field=settings.field_category,
            url_field=settings.field_url,
        )
    )
    records = parser.parse_records(extract_records(raw_payload, settings.news_api_records_path))
    frame = pd.DataFrame(
        {
            "title": [record.title for record in records],
            "text": [record.text for record in records],
            "published_at": [record.published_at for record in records],
            "source": [record.source for record in records],
            "category": [record.category for record in records],
        }
    )
    features = FeatureBuilder().transform(frame)
    scores = bundle.pipeline.predict_proba(features)[:, 1]
    predictions = (scores >= bundle.threshold).astype(int)
    print(json.dumps([{"score": float(score), "prediction": int(pred)} for score, pred in zip(scores, predictions)], indent=2))


if __name__ == "__main__":
    main()
