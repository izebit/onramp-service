# onramp

FastAPI stub with Poetry, type hints, and pydantic-settings. Python 3.14.

## Setup

```bash
poetry install
```

## Run

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Config

Settings are loaded from environment variables or a `.env` file (see `app/config.py`). Options:

- `APP_NAME` (default: `onramp`)
- `DEBUG` (default: `false`)
- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8000`)
- `SIGNATURE_VALID_SECONDS` (default: `300`) — how long a quote signature is valid

## Endpoints

- `GET /` — welcome message
- `GET /health` — health check
