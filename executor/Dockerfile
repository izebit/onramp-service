# Build from repo root: docker build -f executor/Dockerfile .
FROM python:3.14

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry

# Copy shared libs (executor uses backoff, step_processor)
COPY libs/backoff libs/backoff
COPY libs/step_processor libs/step_processor

COPY executor/pyproject.toml executor/poetry.lock executor/
COPY executor/ executor/

RUN cd executor && poetry config virtualenvs.create false \
    && poetry install --no-interaction --without dev

WORKDIR /app/executor

EXPOSE 8002

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8002"]
