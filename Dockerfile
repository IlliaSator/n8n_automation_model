FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY n8n ./n8n

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

CMD ["python", "scripts/run_pipeline.py", "--mode", "schedule"]
