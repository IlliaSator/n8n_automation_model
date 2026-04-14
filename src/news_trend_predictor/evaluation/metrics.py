from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, precision_recall_curve, roc_auc_score


@dataclass(slots=True)
class Metrics:
    pr_auc: float
    roc_auc: float
    f1: float
    accuracy: float

    def to_dict(self) -> dict[str, float]:
        return {
            "pr_auc": self.pr_auc,
            "roc_auc": self.roc_auc,
            "f1": self.f1,
            "accuracy": self.accuracy,
        }


def find_best_threshold(y_true: np.ndarray, scores: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    if thresholds.size == 0:
        return 0.5

    f1_scores = 2 * precision[:-1] * recall[:-1] / np.clip(precision[:-1] + recall[:-1], 1e-12, None)
    best_idx = int(np.nanargmax(f1_scores))
    return float(thresholds[best_idx])


def compute_classification_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> Metrics:
    predictions = (scores >= threshold).astype(int)
    if len(np.unique(y_true)) < 2:
        roc_auc = float("nan")
    else:
        roc_auc = float(roc_auc_score(y_true, scores))
    return Metrics(
        pr_auc=float(average_precision_score(y_true, scores)),
        roc_auc=roc_auc,
        f1=float(f1_score(y_true, predictions, zero_division=0)),
        accuracy=float(accuracy_score(y_true, predictions)),
    )
