from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.evaluation.metrics import Metrics, compute_classification_metrics, find_best_threshold
from news_trend_predictor.features.builder import FeatureBuilder

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ModelBundle:
    version: str
    trained_at: str
    threshold: float
    pipeline: Pipeline
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class TrainArtifacts:
    model_bundle: ModelBundle
    metrics: Metrics
    validation_threshold: float
    train_size: int
    val_size: int
    test_size: int


class ModelTrainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.feature_builder = FeatureBuilder()

    def train(self, frame: pd.DataFrame) -> TrainArtifacts:
        train_frame, val_frame, test_frame = self._time_split(frame)

        train_x = self.feature_builder.transform(train_frame)
        val_x = self.feature_builder.transform(val_frame)
        test_x = self.feature_builder.transform(test_frame)

        model = self._build_pipeline()
        model.fit(train_x, train_frame["target"])

        val_scores = model.predict_proba(val_x)[:, 1]
        threshold = find_best_threshold(val_frame["target"].to_numpy(), val_scores)

        test_scores = model.predict_proba(test_x)[:, 1]
        metrics = compute_classification_metrics(test_frame["target"].to_numpy(), test_scores, threshold=threshold)
        version = datetime.now(timezone.utc).strftime("model_%Y%m%dT%H%M%SZ")

        bundle = ModelBundle(
            version=version,
            trained_at=datetime.now(timezone.utc).isoformat(),
            threshold=threshold,
            pipeline=model,
            metrics=metrics.to_dict(),
        )
        LOGGER.info("Candidate %s trained with PR-AUC %.4f", version, metrics.pr_auc)
        return TrainArtifacts(
            model_bundle=bundle,
            metrics=metrics,
            validation_threshold=threshold,
            train_size=len(train_frame),
            val_size=len(val_frame),
            test_size=len(test_frame),
        )

    def evaluate_bundle(self, bundle: ModelBundle, frame: pd.DataFrame) -> Metrics:
        features = self.feature_builder.transform(frame)
        scores = bundle.pipeline.predict_proba(features)[:, 1]
        return compute_classification_metrics(frame["target"].to_numpy(), scores, threshold=bundle.threshold)

    def _build_pipeline(self) -> Pipeline:
        text_features = "combined_text"
        numeric_features = ["title_length", "text_length", "published_hour", "published_dayofweek"]
        categorical_features = ["source", "category"]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "text",
                    TfidfVectorizer(max_features=self.settings.tfidf_max_features, ngram_range=(1, self.settings.tfidf_ngram_max)),
                    text_features,
                ),
                ("numeric", "passthrough", numeric_features),
                ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ]
        )

        classifier = LogisticRegression(
            C=self.settings.classifier_c,
            class_weight="balanced",
            max_iter=1000,
            random_state=self.settings.random_state,
        )
        return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])

    def _time_split(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if len(frame) < 8:
            raise ValueError("At least 8 records are required to create a stable time-based split.")

        ordered = frame.sort_values("published_at", kind="stable").reset_index(drop=True)
        n_rows = len(ordered)
        train_end = max(1, int(n_rows * self.settings.train_fraction))
        val_end = max(train_end + 1, int(n_rows * (self.settings.train_fraction + self.settings.val_fraction)))
        val_end = min(val_end, n_rows - 1)

        train_frame = ordered.iloc[:train_end]
        val_frame = ordered.iloc[train_end:val_end]
        test_frame = ordered.iloc[val_end:]

        for split_name, split_frame in {"train": train_frame, "val": val_frame, "test": test_frame}.items():
            if split_frame.empty:
                raise ValueError(f"{split_name} split is empty. Adjust dataset size or split fractions.")

        return train_frame, val_frame, test_frame
