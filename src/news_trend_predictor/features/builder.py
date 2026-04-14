from __future__ import annotations

import pandas as pd

from news_trend_predictor.preprocessing.text import clean_text


class FeatureBuilder:
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        features = frame.copy()
        features["title_clean"] = features["title"].map(clean_text)
        features["text_clean"] = features["text"].map(clean_text)
        features["combined_text"] = (features["title_clean"] + " " + features["text_clean"]).str.strip()
        features["title_length"] = features["title_clean"].str.len()
        features["text_length"] = features["text_clean"].str.len()
        features["published_hour"] = pd.to_datetime(features["published_at"]).dt.hour.fillna(0).astype(int)
        features["published_dayofweek"] = pd.to_datetime(features["published_at"]).dt.dayofweek.fillna(0).astype(int)
        features["source"] = features["source"].fillna("unknown").replace("", "unknown")
        features["category"] = features["category"].fillna("unknown").replace("", "unknown")
        return features[
            [
                "combined_text",
                "title_length",
                "text_length",
                "published_hour",
                "published_dayofweek",
                "source",
                "category",
            ]
        ]
