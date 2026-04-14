from news_trend_predictor.google_sheets.client import build_run_log_row


def test_google_sheets_row_order_is_stable() -> None:
    row = build_run_log_row(
        {
            "timestamp": "2026-04-14T10:00:00Z",
            "run_id": "abc123",
            "number_of_records": 18,
            "model_version_old": "model_old",
            "model_version_new": "model_new",
            "pr_auc_old": "0.7000",
            "pr_auc_new": "0.7500",
            "roc_auc_old": "0.8000",
            "roc_auc_new": "0.8200",
            "f1_old": "0.6100",
            "f1_new": "0.6500",
            "threshold": "0.4400",
            "deploy_decision": "deploy",
            "status": "success",
            "error_message": "",
        }
    )

    assert row == [
        "2026-04-14T10:00:00Z",
        "abc123",
        "18",
        "model_old",
        "model_new",
        "0.7000",
        "0.7500",
        "0.8000",
        "0.8200",
        "0.6100",
        "0.6500",
        "0.4400",
        "deploy",
        "success",
        "",
    ]
