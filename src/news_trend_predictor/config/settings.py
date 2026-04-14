from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "News Trend Predictor"
    log_level: str = "INFO"

    news_api_base_url: str | None = None
    news_api_endpoint: str = "/news"
    news_api_key: str | None = None
    news_api_timeout_seconds: int = 20
    news_api_records_path: str = "articles"
    news_api_sample_path: str = "data/sample_news.json"

    field_id: str = "id"
    field_title: str = "title"
    field_text: str = "text"
    field_summary: str = "summary"
    field_published_at: str = "published_at"
    field_source: str = "source"
    field_category: str = "category"
    field_url: str = "url"
    field_target: str | None = None
    field_trend_score: str | None = None

    trend_score_threshold: float = 0.8
    trend_window_hours: int = 24
    trend_proxy_percentile: float = 0.75

    train_fraction: float = 0.7
    val_fraction: float = 0.15
    min_positive_samples: int = 2

    tfidf_max_features: int = 4000
    tfidf_ngram_max: int = 2
    classifier_c: float = 1.0
    random_state: int = 42

    primary_metric: str = "pr_auc"
    min_pr_auc_improvement: float = 0.01

    artifacts_dir: str = "artifacts"
    active_model_filename: str = "active_model.joblib"
    candidate_model_filename: str = "candidate_model.joblib"
    backup_model_filename: str = "active_model.backup.joblib"
    latest_dataset_filename: str = "latest_dataset.csv"

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    enable_internal_telegram_notifier: bool = True

    google_service_account_json: str | None = None
    google_sheet_id: str | None = None
    google_sheet_name: str = "pipeline_runs"
    enable_internal_google_sheets_logger: bool = True

    schedule_cron: str = "0 * * * *"

    @property
    def artifacts_path(self) -> Path:
        return Path(self.artifacts_dir)

    @property
    def active_model_path(self) -> Path:
        return self.artifacts_path / self.active_model_filename

    @property
    def candidate_model_path(self) -> Path:
        return self.artifacts_path / self.candidate_model_filename

    @property
    def backup_model_path(self) -> Path:
        return self.artifacts_path / self.backup_model_filename

    @property
    def latest_dataset_path(self) -> Path:
        return self.artifacts_path / self.latest_dataset_filename


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
