from news_trend_predictor.config.settings import Settings
from news_trend_predictor.deployment.service import DeploymentService
from news_trend_predictor.evaluation.metrics import Metrics
from news_trend_predictor.training.trainer import ModelBundle


class DummyRegistry:
    def __init__(self) -> None:
        self.saved = False
        self.promoted = False

    def save_candidate(self, bundle: ModelBundle) -> None:
        self.saved = True

    def promote_candidate(self) -> None:
        self.promoted = True


def make_bundle(version: str) -> ModelBundle:
    return ModelBundle(version=version, trained_at="2026-04-14T00:00:00Z", threshold=0.5, pipeline=None, metrics={})


def test_deployment_service_promotes_better_candidate() -> None:
    registry = DummyRegistry()
    service = DeploymentService(Settings(min_pr_auc_improvement=0.01), registry)

    result = service.decide_and_deploy(
        candidate_bundle=make_bundle("candidate"),
        candidate_metrics=Metrics(pr_auc=0.8, roc_auc=0.8, f1=0.7, accuracy=0.75),
        active_bundle=make_bundle("active"),
        active_metrics=Metrics(pr_auc=0.7, roc_auc=0.79, f1=0.65, accuracy=0.72),
    )

    assert registry.saved is True
    assert registry.promoted is True
    assert result.deployed is True


def test_deployment_service_keeps_candidate_without_promotion_if_not_better() -> None:
    registry = DummyRegistry()
    service = DeploymentService(Settings(min_pr_auc_improvement=0.1), registry)

    result = service.decide_and_deploy(
        candidate_bundle=make_bundle("candidate"),
        candidate_metrics=Metrics(pr_auc=0.72, roc_auc=0.8, f1=0.7, accuracy=0.75),
        active_bundle=make_bundle("active"),
        active_metrics=Metrics(pr_auc=0.7, roc_auc=0.79, f1=0.65, accuracy=0.72),
    )

    assert registry.saved is True
    assert registry.promoted is False
    assert result.deployed is False
