from __future__ import annotations

from dataclasses import dataclass

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.evaluation.comparison import should_deploy_candidate
from news_trend_predictor.evaluation.metrics import Metrics
from news_trend_predictor.model_registry.local import LocalModelRegistry
from news_trend_predictor.training.trainer import ModelBundle


@dataclass(slots=True)
class DeploymentResult:
    deployed: bool
    reason: str
    old_version: str | None
    new_version: str


class DeploymentService:
    def __init__(self, settings: Settings, registry: LocalModelRegistry) -> None:
        self.settings = settings
        self.registry = registry

    def decide_and_deploy(
        self,
        candidate_bundle: ModelBundle,
        candidate_metrics: Metrics,
        active_bundle: ModelBundle | None,
        active_metrics: Metrics | None,
    ) -> DeploymentResult:
        self.registry.save_candidate(candidate_bundle)
        should_deploy, reason = should_deploy_candidate(candidate_metrics, active_metrics, self.settings)
        if should_deploy:
            self.registry.promote_candidate()

        return DeploymentResult(
            deployed=should_deploy,
            reason=reason,
            old_version=active_bundle.version if active_bundle else None,
            new_version=candidate_bundle.version,
        )
