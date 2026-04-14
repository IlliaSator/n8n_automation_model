from __future__ import annotations

import argparse
import base64
import json
import math

from news_trend_predictor.data_ingestion.client import NewsAPIClient
from news_trend_predictor.config.settings import get_settings
from news_trend_predictor.logging_utils import configure_logging
from news_trend_predictor.pipeline.orchestrator import PipelineRunResult, PipelineRunner


def _safe_float(value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def _serialize_result(result: PipelineRunResult) -> dict[str, object]:
    return {
        "run_id": result.run_id,
        "status": result.status,
        "record_count": result.record_count,
        "threshold": _safe_float(result.threshold),
        "error_message": result.error_message,
        "deployment": {
            "deployed": result.deployment.deployed if result.deployment else False,
            "reason": result.deployment.reason if result.deployment else "",
            "old_version": result.deployment.old_version if result.deployment else None,
            "new_version": result.deployment.new_version if result.deployment else None,
        },
        "candidate_metrics": {
            "pr_auc": _safe_float(result.candidate_metrics.pr_auc) if result.candidate_metrics else None,
            "roc_auc": _safe_float(result.candidate_metrics.roc_auc) if result.candidate_metrics else None,
            "f1": _safe_float(result.candidate_metrics.f1) if result.candidate_metrics else None,
            "accuracy": _safe_float(result.candidate_metrics.accuracy) if result.candidate_metrics else None,
        },
        "active_metrics": {
            "pr_auc": _safe_float(result.active_metrics.pr_auc) if result.active_metrics else None,
            "roc_auc": _safe_float(result.active_metrics.roc_auc) if result.active_metrics else None,
            "f1": _safe_float(result.active_metrics.f1) if result.active_metrics else None,
            "accuracy": _safe_float(result.active_metrics.accuracy) if result.active_metrics else None,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pipeline and return structured JSON output for n8n.")
    parser.add_argument("--payload-b64", default=None, help="Base64-encoded raw API JSON payload.")
    return parser.parse_args()


def _decode_payload_records(payload_b64: str, settings) -> list[dict]:
    raw_payload = base64.b64decode(payload_b64.encode("utf-8")).decode("utf-8")
    parsed_payload = json.loads(raw_payload)
    return NewsAPIClient(settings).extract_records(parsed_payload)


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    raw_records_override = _decode_payload_records(args.payload_b64, settings) if args.payload_b64 else None
    result = PipelineRunner(settings).run(raw_records_override=raw_records_override)
    print(json.dumps(_serialize_result(result), ensure_ascii=True))


if __name__ == "__main__":
    main()
