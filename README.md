# News Trend Predictor

Minimalistic, production-style ML pipeline that predicts whether a news item will trend within a configurable time window. The project is intentionally lean: scikit-learn baseline, local model registry, adapters for Telegram and Google Sheets, time-based validation, and Docker-first execution without heavy infrastructure.

## Project Structure

```text
.
|-- Dockerfile
|-- README.md
|-- data/
|   `-- sample_news.json
|-- n8n/
|   `-- workflows/
|       `-- news-trend-predictor.json
|-- artifacts/
|-- scripts/
|   |-- infer.py
|   |-- run_pipeline.py
|   `-- train.py
|-- src/
|   `-- news_trend_predictor/
|       |-- config/
|       |   `-- settings.py
|       |-- data_ingestion/
|       |   |-- client.py
|       |   |-- dataset.py
|       |   `-- schemas.py
|       |-- deployment/
|       |   `-- service.py
|       |-- evaluation/
|       |   |-- comparison.py
|       |   `-- metrics.py
|       |-- features/
|       |   `-- builder.py
|       |-- google_sheets/
|       |   `-- client.py
|       |-- model_registry/
|       |   `-- local.py
|       |-- notifications/
|       |   `-- telegram.py
|       |-- pipeline/
|       |   `-- orchestrator.py
|       |-- preprocessing/
|       |   `-- text.py
|       |-- training/
|       |   `-- trainer.py
|       `-- logging_utils.py
`-- tests/
    |-- test_deployment_logic.py
    |-- test_google_sheets_payload.py
    |-- test_metric_comparison.py
    `-- test_preprocessing.py
```

## What It Does

1. Pulls JSON news data from an API or local sample payload.
2. Parses heterogeneous API payloads through a configurable `NewsAPIClient` + field mapping.
3. Builds a dataset and derives a binary target:
   - explicit label if `FIELD_TARGET` is provided,
   - score threshold if `FIELD_TREND_SCORE` is configured,
   - fallback proxy target based on future source/category velocity inside a trend window.
4. Cleans text and generates baseline features:
   - TF-IDF over title + body/summary,
   - text length,
   - title length,
   - publication hour,
   - day of week,
   - source,
   - category.
5. Trains a `LogisticRegression` classifier with a strict time-based split.
6. Tunes the decision threshold on the validation split.
7. Evaluates the candidate and the current active model on the same holdout slice.
8. Promotes the candidate only if PR-AUC improves by at least `MIN_PR_AUC_IMPROVEMENT`.
9. Sends Telegram notifications and appends run logs to Google Sheets when credentials are available.

## Pipeline Flow

```text
News API / sample JSON
        |
        v
  NewsAPIClient
        |
        v
 NewsResponseParser
        |
        v
  DatasetBuilder ----> target generation
        |
        v
  FeatureBuilder
        |
        v
  ModelTrainer
        |
        +--> validation threshold tuning
        |
        v
  candidate model
        |
        +--> compare with active model
        |
        v
 DeploymentService
        |
        +--> LocalModelRegistry
        +--> TelegramNotifier
        `--> GoogleSheetsLogger
```

## Stack

- Python 3.11+
- scikit-learn
- pandas / numpy
- Pydantic Settings
- APScheduler
- requests
- gspread
- pytest
- Docker

## Local Run

### 1. Install

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
```

### 2. Configure environment

```bash
copy .env.example .env
```

If `NEWS_API_BASE_URL` is empty, the pipeline uses `data/sample_news.json` for a local smoke run.

To connect a real news portal API:

1. Set `NEWS_API_BASE_URL`
2. Set `NEWS_API_ENDPOINT`
3. Set `NEWS_API_RECORDS_PATH` to the JSON list path, for example `articles` or `data.items`
4. Map portal fields through `FIELD_*` variables
5. Optionally provide `FIELD_TARGET` or `FIELD_TREND_SCORE` if the API already contains labels or trend scores

### 3. Run one pipeline execution

```bash
python scripts/run_pipeline.py --mode once
```

### 4. Start local scheduler

```bash
python scripts/run_pipeline.py --mode schedule
```

## Docker

Build:

```bash
docker build -t news-trend-predictor .
```

Run once:

```bash
docker run --rm --env-file .env news-trend-predictor python scripts/run_pipeline.py --mode once
```

Run scheduler:

```bash
docker run --rm --env-file .env news-trend-predictor
```

## CI

GitHub Actions are included in `.github/workflows`.

CI:

- runs on `push` to `main` or `master`
- runs on every pull request
- installs the project
- executes `pytest`
- runs one pipeline smoke test with the bundled sample dataset
- verifies `docker build`

GitHub Actions notes:

- no application secrets are stored in the repository; runtime secrets stay in `.env` or GitHub Secrets

## Telegram Quick Start

1. Create a bot with `@BotFather`
2. Copy the bot token into `TELEGRAM_BOT_TOKEN`
3. Send at least one message to the bot from the target chat
4. Open:

```text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

5. Find `chat.id` in the JSON response and copy it into `TELEGRAM_CHAT_ID`
6. Run the pipeline locally or in Docker

Minimal `.env` fields for Telegram test:

```env
NEWS_API_BASE_URL=
NEWS_API_RECORDS_PATH=articles
NEWS_API_SAMPLE_PATH=data/sample_news.json
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Docker test command:

```bash
docker run --rm --env-file .env news-trend-predictor python scripts/run_pipeline.py --mode once
```

Expected result:

- container logs show a successful pipeline run
- Telegram receives a success message with run id, record count, PR-AUC, and deploy decision

## Environment Variables

Core:

- `NEWS_API_BASE_URL`: base URL of the news API. Leave empty to use the bundled sample payload.
- `NEWS_API_ENDPOINT`: endpoint appended to the base URL.
- `NEWS_API_RECORDS_PATH`: dot path to the list of articles inside the JSON response.
- `NEWS_API_KEY`: optional bearer token for the API.

Field mapping:

- `FIELD_ID`
- `FIELD_TITLE`
- `FIELD_TEXT`
- `FIELD_SUMMARY`
- `FIELD_PUBLISHED_AT`
- `FIELD_SOURCE`
- `FIELD_CATEGORY`
- `FIELD_URL`
- `FIELD_TARGET`
- `FIELD_TREND_SCORE`

Modeling:

- `TREND_WINDOW_HOURS`
- `TREND_PROXY_PERCENTILE`
- `TRAIN_FRACTION`
- `VAL_FRACTION`
- `MIN_PR_AUC_IMPROVEMENT`
- `TFIDF_MAX_FEATURES`
- `TFIDF_NGRAM_MAX`

Integrations:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SHEET_NAME`

Scheduling:

- `SCHEDULE_CRON`

## Training Details

- Task: binary classification
- Primary metric: PR-AUC
- Additional metrics: ROC-AUC, F1, accuracy
- Split strategy: chronological train/validation/test split
- Threshold tuning: performed on validation data using best F1 from the precision-recall curve
- Baseline model: TF-IDF + metadata features + logistic regression

## Model Comparison and Deployment

- Candidate model is always saved as `artifacts/candidate_model.joblib`
- Active model lives at `artifacts/active_model.joblib`
- Candidate is promoted only if:
  - there is no active model yet, or
  - `candidate_pr_auc - active_pr_auc >= MIN_PR_AUC_IMPROVEMENT`
- Promotion uses a backup file and restores the previous model if replacement fails

## Telegram and Google Sheets

Telegram:

- Sent on pipeline success
- Includes deployment result and candidate PR-AUC
- Sent on pipeline failure with the error message
- If Telegram credentials are missing, notification is skipped without failing the pipeline

Google Sheets:

- Uses a service account JSON provided through `GOOGLE_SERVICE_ACCOUNT_JSON`
- Appends one row per run
- Logs timestamp, versions, metrics, threshold, deployment decision, status, and error text

## Example Logs

```text
2026-04-14 11:08:22,117 | INFO | news_trend_predictor.data_ingestion.client | NEWS_API_BASE_URL is not configured. Using sample payload from data/sample_news.json
2026-04-14 11:08:22,149 | INFO | news_trend_predictor.data_ingestion.dataset | Built dataset with 18 rows and 5 positive targets
2026-04-14 11:08:22,462 | INFO | news_trend_predictor.training.trainer | Candidate model_20260414T080822Z trained with PR-AUC 0.7812
```

## Tests

```bash
pytest
```

Covered areas:

- text preprocessing
- model comparison logic
- deployment decision flow
- Google Sheets row formatting

## Orchestration Notes

This project includes a real `n8n` workflow file, while keeping the ML logic in Python.

What is implemented:

- a Python orchestrator with explicit pipeline steps
- adapter-style integrations for API ingestion, Telegram, Google Sheets, and local model registry
- scheduler-driven execution through APScheduler

Conceptual mapping to `n8n`:

- `NewsAPIClient` acts like an HTTP node
- `DatasetBuilder`, `FeatureBuilder`, and `ModelTrainer` act like transformation nodes
- `DeploymentService` acts like a decision node
- `TelegramNotifier` and `GoogleSheetsLogger` act like output nodes

The current setup uses `n8n` for visual orchestration and Python for ML execution, which keeps the automation layer clear without moving model training logic into low-level node scripts.

## n8n Automation

The repository now includes an importable n8n workflow.

Files to use:

- workflow JSON: `n8n/workflows/news-trend-predictor.json`
- n8n-specific notes: `n8n/README.md`

The workflow provides visual connections for:

- manual trigger
- schedule trigger
- HTTP request to the news API
- pipeline execution
- JSON result parsing
- success vs failure branching
- deployed vs not deployed branching
- Telegram notification nodes
- Google Sheets append node

Visual flow:

```text
Manual Trigger ----\
                    -> HTTP Request - News API -> Run Pipeline -> Parse Result -> Pipeline Success?
Schedule Trigger --/                                                   | false -> Build Failure Message -> Telegram - Failure
                                                                       |
                                                                       true -> Model Improved?
                                                                               | true  -> Build Deploy Message  -> Telegram - Deploy
                                                                               | false -> Build Success Message -> Telegram - Success
Parse Result ----------------------------------------------------------> Prepare Sheets Row -> Google Sheets - Append Run
```

How to use it in n8n:

1. Open n8n
2. Import `n8n/workflows/news-trend-predictor.json`
3. Configure `PROJECT_ROOT` in the environment used by n8n
4. Configure Telegram credentials in the three Telegram nodes
5. Configure Google Sheets credentials in the Google Sheets node
6. Set the required environment variables used in the expressions

How to see the workflow visually:

1. Start n8n Desktop or run `docker run --rm -it -p 5678:5678 n8nio/n8n`
2. Open `http://localhost:5678`
3. Use `Import from File`
4. Select `n8n/workflows/news-trend-predictor.json`

If you only want to inspect the visual node graph, importing the JSON is enough.
If you want to execute it, n8n needs Python, project dependencies, and access to this repo.

Recommended environment variables for n8n execution:

- `PROJECT_ROOT`: root path of this project
- `NEWS_API_BASE_URL`
- `NEWS_API_ENDPOINT`
- `NEWS_API_KEY`
- `TELEGRAM_CHAT_ID`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SHEET_NAME`

Why the workflow uses a Python command node:

- the ML business logic stays versioned in Python modules
- n8n handles orchestration and visual automation
- the workflow remains easy to understand and modify without duplicating training logic inside n8n

The workflow calls:

```bash
python scripts/run_pipeline_json.py
```

That script prints structured JSON so n8n can branch on:

- `status`
- `deployment.deployed`
- `candidate_metrics.pr_auc`
- `deployment.reason`
- `error_message`

## Why This Project Is Middle-Level

- It is modular, but intentionally avoids platform-heavy infrastructure.
- It contains a real training/evaluation/deployment loop instead of a notebook-only workflow.
- It separates external integrations behind adapters.
- It handles threshold tuning, time-based validation, promotion rules, rollback, and artifacts.
- It is easy to run locally, but structured so the same code can move into a larger production environment later.
