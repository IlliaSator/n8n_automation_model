from __future__ import annotations

import json
import logging
from typing import Any

import gspread

from news_trend_predictor.config.settings import Settings

LOGGER = logging.getLogger(__name__)


def build_run_log_row(payload: dict[str, Any]) -> list[str]:
    ordered_fields = [
        "timestamp",
        "run_id",
        "number_of_records",
        "model_version_old",
        "model_version_new",
        "pr_auc_old",
        "pr_auc_new",
        "roc_auc_old",
        "roc_auc_new",
        "f1_old",
        "f1_new",
        "threshold",
        "deploy_decision",
        "status",
        "error_message",
    ]
    return [str(payload.get(field, "")) for field in ordered_fields]


class GoogleSheetsLogger:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def append_run(self, payload: dict[str, Any]) -> None:
        if not self.settings.google_service_account_json or not self.settings.google_sheet_id:
            LOGGER.info("Google Sheets is not configured. Skipping run log append.")
            return

        credentials = json.loads(self.settings.google_service_account_json)
        client = gspread.service_account_from_dict(credentials)
        worksheet = client.open_by_key(self.settings.google_sheet_id).worksheet(self.settings.google_sheet_name)
        worksheet.append_row(build_run_log_row(payload), value_input_option="USER_ENTERED")
