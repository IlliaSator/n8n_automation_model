from __future__ import annotations

import logging
from datetime import timedelta

import numpy as np
import pandas as pd

from news_trend_predictor.config.settings import Settings
from news_trend_predictor.data_ingestion.schemas import NewsRecord

LOGGER = logging.getLogger(__name__)


class DatasetBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(self, records: list[NewsRecord]) -> pd.DataFrame:
        frame = pd.DataFrame(
            {
                "id": [record.record_id for record in records],
                "title": [record.title for record in records],
                "text": [record.text for record in records],
                "published_at": [pd.Timestamp(record.published_at).tz_localize(None) if pd.Timestamp(record.published_at).tzinfo else pd.Timestamp(record.published_at) for record in records],
                "source": [record.source for record in records],
                "category": [record.category for record in records],
                "url": [record.url for record in records],
                "raw_payload": [record.raw_payload for record in records],
            }
        ).sort_values("published_at", kind="stable")

        frame["target"] = self._build_target(frame)
        LOGGER.info("Built dataset with %s rows and %s positive targets", len(frame), int(frame["target"].sum()))
        return frame.reset_index(drop=True)

    def _build_target(self, frame: pd.DataFrame) -> pd.Series:
        explicit_labels = self._extract_explicit_labels(frame)
        if explicit_labels is not None:
            return explicit_labels

        proxy_scores = self._build_proxy_trend_scores(frame)
        threshold = float(proxy_scores.quantile(self.settings.trend_proxy_percentile))
        labels = (proxy_scores >= threshold).astype(int)

        if int(labels.sum()) < self.settings.min_positive_samples:
            top_indices = proxy_scores.nlargest(self.settings.min_positive_samples).index
            labels.loc[:] = 0
            labels.loc[top_indices] = 1

        return labels.astype(int)

    def _extract_explicit_labels(self, frame: pd.DataFrame) -> pd.Series | None:
        target_field = self.settings.field_target or self._detect_common_field(frame, ["is_trending", "target"])
        score_field = self.settings.field_trend_score or self._detect_common_field(frame, ["trend_score", "score"])

        if target_field:
            labels = frame["raw_payload"].apply(lambda item: int(bool(item.get(target_field, 0))))
            return labels.astype(int)

        if score_field:
            return frame["raw_payload"].apply(
                lambda item: int(float(item.get(score_field, 0.0)) >= self.settings.trend_score_threshold)
            )

        return None

    @staticmethod
    def _detect_common_field(frame: pd.DataFrame, candidates: list[str]) -> str | None:
        for field_name in candidates:
            if frame["raw_payload"].map(lambda item: field_name in item).any():
                return field_name
        return None

    def _build_proxy_trend_scores(self, frame: pd.DataFrame) -> pd.Series:
        horizon = timedelta(hours=self.settings.trend_window_hours)
        scores: list[float] = []
        timestamps = frame["published_at"]

        for index, row in frame.iterrows():
            upper_bound = row["published_at"] + horizon
            future_mask = (timestamps > row["published_at"]) & (timestamps <= upper_bound)
            future_slice = frame.loc[future_mask]

            same_source = int((future_slice["source"] == row["source"]).sum())
            same_category = int((future_slice["category"] == row["category"]).sum())
            title_signal = len(row["title"].split()) / 10.0
            scores.append(same_source * 0.6 + same_category * 0.4 + title_signal)

        return pd.Series(scores, index=frame.index, dtype=float)
