from news_trend_predictor.config.settings import Settings
from news_trend_predictor.evaluation.comparison import should_deploy_candidate
from news_trend_predictor.evaluation.metrics import Metrics


def test_should_deploy_when_pr_auc_improves_enough() -> None:
    settings = Settings(min_pr_auc_improvement=0.02)
    decision, reason = should_deploy_candidate(
        candidate_metrics=Metrics(pr_auc=0.71, roc_auc=0.8, f1=0.6, accuracy=0.7),
        active_metrics=Metrics(pr_auc=0.67, roc_auc=0.79, f1=0.58, accuracy=0.69),
        settings=settings,
    )
    assert decision is True
    assert "improved" in reason


def test_should_not_deploy_when_gain_is_below_threshold() -> None:
    settings = Settings(min_pr_auc_improvement=0.05)
    decision, reason = should_deploy_candidate(
        candidate_metrics=Metrics(pr_auc=0.71, roc_auc=0.8, f1=0.6, accuracy=0.7),
        active_metrics=Metrics(pr_auc=0.69, roc_auc=0.79, f1=0.58, accuracy=0.69),
        settings=settings,
    )
    assert decision is False
    assert "below threshold" in reason
