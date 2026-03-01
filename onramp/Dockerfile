# Build from repo root: docker build -f onramp/Dockerfile .
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY libs/hash libs/hash
COPY onramp/pyproject.toml onramp/poetry.lock onramp/
COPY onramp/ onramp/

RUN cd onramp && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev

WORKDIR /app/onramp

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
