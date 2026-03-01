# Build from repo root: docker build -f webhook/Dockerfile .
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry

# Copy shared libs (webhook uses backoff, hash, step_processor)
COPY libs/backoff libs/backoff
COPY libs/hash libs/hash
COPY libs/step_processor libs/step_processor

COPY webhook/pyproject.toml webhook/poetry.lock webhook/
COPY webhook/ webhook/

RUN cd webhook && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev

WORKDIR /app/webhook

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
