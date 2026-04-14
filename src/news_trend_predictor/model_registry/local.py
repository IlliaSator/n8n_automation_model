from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.training.trainer import ModelBundle


@dataclass(slots=True)
class StoredModelInfo:
    version: str
    threshold: float
    metrics: dict[str, float]
    trained_at: str


class LocalModelRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    def load_active_model(self) -> ModelBundle | None:
        if not self.settings.active_model_path.exists():
            return None
        return joblib.load(self.settings.active_model_path)

    def save_candidate(self, bundle: ModelBundle) -> Path:
        joblib.dump(bundle, self.settings.candidate_model_path)
        return self.settings.candidate_model_path

    def promote_candidate(self) -> None:
        candidate_path = self.settings.candidate_model_path
        active_path = self.settings.active_model_path
        backup_path = self.settings.backup_model_path

        if not candidate_path.exists():
            raise FileNotFoundError("Candidate model does not exist.")

        if active_path.exists():
            active_path.replace(backup_path)

        try:
            candidate_path.replace(active_path)
        except Exception:
            if backup_path.exists():
                backup_path.replace(active_path)
            raise
        finally:
            if backup_path.exists():
                backup_path.unlink(missing_ok=True)

    def save_dataset_snapshot(self, frame: Any) -> Path:
        frame.to_csv(self.settings.latest_dataset_path, index=False)
        return self.settings.latest_dataset_path
