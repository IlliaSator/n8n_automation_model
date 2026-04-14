# n8n Workflow

This folder contains the visual n8n automation workflow for the project:

- `workflows/news-trend-predictor.json`

## What the workflow shows

- manual trigger
- schedule trigger
- pipeline execution
- parsing pipeline JSON output
- branching for success vs failure
- branching for deployed vs not deployed
- prepared payload for Telegram
- prepared payload for Google Sheets

## How to view the workflow

### Option 1. n8n Desktop

1. Install n8n Desktop
2. Open the app
3. Choose import workflow
4. Select `n8n/workflows/news-trend-predictor.json`

### Option 2. n8n in Docker

```bash
docker run --rm -it -p 5678:5678 n8nio/n8n
```

Then open:

```text
http://localhost:5678
```

After that:

1. Create an account in the local n8n UI
2. Click `Import from File`
3. Choose `n8n/workflows/news-trend-predictor.json`

## How to execute it

The workflow runs:

```bash
python scripts/run_pipeline_json.py
```

So for actual execution, n8n must run in an environment that has:

- Python 3.11+
- project dependencies installed
- access to this repository files

The simplest path is:

- run n8n Desktop on the same machine
- open the imported workflow
- point the `Execute Command` node to the repository working directory

If you only want to inspect the visual graph, importing the JSON is enough.
