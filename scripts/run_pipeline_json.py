from __future__ import annotations

import json
import math
from dataclasses import asdict

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


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    result = PipelineRunner(settings).run()
    print(json.dumps(_serialize_result(result), ensure_ascii=True))


if __name__ == "__main__":
    main()
