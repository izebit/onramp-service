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
- `SECRET_KEY` (default: `change-me-in-production`) — secret for JWT validation and quote signing
- `AUTHENTICATION_DISABLED` (default: `false`) — if true, JWT `expiration_at` is not checked
- `DATABASE_URL` (default: `postgresql://postgres:postgres@localhost:5432/onramp`) — PostgreSQL connection string for orders

## Endpoints

- `GET /` — welcome message
- `GET /health` — health check
