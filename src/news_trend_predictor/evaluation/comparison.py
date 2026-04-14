from __future__ import annotations

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.evaluation.metrics import Metrics


def should_deploy_candidate(candidate_metrics: Metrics, active_metrics: Metrics | None, settings: Settings) -> tuple[bool, str]:
    if active_metrics is None:
        return True, "No active model found."

    improvement = candidate_metrics.pr_auc - active_metrics.pr_auc
    if improvement >= settings.min_pr_auc_improvement:
        return True, f"Candidate improved PR-AUC by {improvement:.4f}."

    return False, f"Candidate PR-AUC improvement {improvement:.4f} is below threshold {settings.min_pr_auc_improvement:.4f}."
