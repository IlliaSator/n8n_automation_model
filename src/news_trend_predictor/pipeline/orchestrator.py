from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.data_ingestion.client import NewsAPIClient
from news_trend_predictor.data_ingestion.dataset import DatasetBuilder
from news_trend_predictor.data_ingestion.schemas import NewsFieldMapping, NewsResponseParser
from news_trend_predictor.deployment.service import DeploymentResult, DeploymentService
from news_trend_predictor.evaluation.metrics import Metrics
from news_trend_predictor.google_sheets.client import GoogleSheetsLogger
from news_trend_predictor.model_registry.local import LocalModelRegistry
from news_trend_predictor.notifications.telegram import TelegramNotifier
from news_trend_predictor.training.trainer import ModelTrainer

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineRunResult:
    run_id: str
    status: str
    deployment: DeploymentResult | None
    candidate_metrics: Metrics | None
    active_metrics: Metrics | None
    record_count: int
    threshold: float | None = None
    error_message: str = ""


class PipelineRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = NewsAPIClient(settings)
        self.parser = NewsResponseParser(
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
        self.dataset_builder = DatasetBuilder(settings)
        self.trainer = ModelTrainer(settings)
        self.registry = LocalModelRegistry(settings)
        self.deployment_service = DeploymentService(settings, self.registry)
        self.telegram = TelegramNotifier(settings)
        self.sheets = GoogleSheetsLogger(settings)

    def run(self) -> PipelineRunResult:
        run_id = uuid4().hex[:12]
        timestamp = datetime.now(timezone.utc).isoformat()
        candidate_metrics = None
        active_metrics = None
        deployment = None
        record_count = 0

        try:
            raw_records = self.client.fetch_raw_records()
            records = self.parser.parse_records(raw_records)
            dataset = self.dataset_builder.build(records)
            record_count = len(dataset)
            self.registry.save_dataset_snapshot(dataset)

            train_artifacts = self.trainer.train(dataset)
            candidate_metrics = train_artifacts.metrics

            active_bundle = self.registry.load_active_model()
            if active_bundle:
                _, _, test_frame = self.trainer._time_split(dataset)
                active_metrics = self.trainer.evaluate_bundle(active_bundle, test_frame)

            deployment = self.deployment_service.decide_and_deploy(
                candidate_bundle=train_artifacts.model_bundle,
                candidate_metrics=train_artifacts.metrics,
                active_bundle=active_bundle,
                active_metrics=active_metrics,
            )

            result = PipelineRunResult(
                run_id=run_id,
                status="success",
                deployment=deployment,
                candidate_metrics=candidate_metrics,
                active_metrics=active_metrics,
                record_count=record_count,
                threshold=train_artifacts.model_bundle.threshold,
            )
            self._log_result(timestamp, result)
            self._notify_success(result)
            return result
        except Exception as exc:
            error_message = str(exc)
            LOGGER.exception("Pipeline run failed")
            result = PipelineRunResult(
                run_id=run_id,
                status="failed",
                deployment=deployment,
                candidate_metrics=candidate_metrics,
                active_metrics=active_metrics,
                record_count=record_count,
                threshold=None,
                error_message=error_message,
            )
            self._log_result(timestamp, result)
            self._notify_failure(result)
            return result

    def _log_result(self, timestamp: str, result: PipelineRunResult) -> None:
        payload = {
            "timestamp": timestamp,
            "run_id": result.run_id,
            "number_of_records": result.record_count,
            "model_version_old": result.deployment.old_version if result.deployment else "",
            "model_version_new": result.deployment.new_version if result.deployment else "",
            "pr_auc_old": f"{result.active_metrics.pr_auc:.4f}" if result.active_metrics else "",
            "pr_auc_new": f"{result.candidate_metrics.pr_auc:.4f}" if result.candidate_metrics else "",
            "roc_auc_old": f"{result.active_metrics.roc_auc:.4f}" if result.active_metrics else "",
            "roc_auc_new": f"{result.candidate_metrics.roc_auc:.4f}" if result.candidate_metrics else "",
            "f1_old": f"{result.active_metrics.f1:.4f}" if result.active_metrics else "",
            "f1_new": f"{result.candidate_metrics.f1:.4f}" if result.candidate_metrics else "",
            "threshold": f"{result.threshold:.4f}" if result.threshold is not None else "",
            "deploy_decision": result.deployment.reason if result.deployment else "no decision",
            "status": result.status,
            "error_message": result.error_message,
        }
        self.sheets.append_run(payload)

    def _notify_success(self, result: PipelineRunResult) -> None:
        if not result.deployment or not result.candidate_metrics:
            return
        message = (
            f"[{self.settings.project_name}] Pipeline succeeded\n"
            f"Run ID: {result.run_id}\n"
            f"Records: {result.record_count}\n"
            f"Candidate PR-AUC: {result.candidate_metrics.pr_auc:.4f}\n"
            f"Deployment: {'yes' if result.deployment.deployed else 'no'}\n"
            f"Reason: {result.deployment.reason}"
        )
        self.telegram.send(message)

    def _notify_failure(self, result: PipelineRunResult) -> None:
        message = (
            f"[{self.settings.project_name}] Pipeline failed\n"
            f"Run ID: {result.run_id}\n"
            f"Error: {result.error_message}"
        )
        self.telegram.send(message)
