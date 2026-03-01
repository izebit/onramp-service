# webhook

Webhook registration service: JWT-protected `POST /api/v1/clients/webhooks` with body `{ "url": "<URL>" }`. Stores `client_ref` (from JWT) and `url` in the database.

## Setup

```bash
poetry install
```

## Run

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Migrations run on startup. To run manually: `poetry run alembic upgrade head`.

## Config

- `SECRET_KEY` — JWT validation (min 32 bytes)
- `DATABASE_URL` — PostgreSQL connection string
- `AUTHENTICATION_DISABLED` — if true, JWT expiration is not checked

## Endpoints

- `POST /api/v1/clients/webhooks` — register webhook URL (requires `Authorization: Bearer <JWT>`). Body: `{ "url": "https://...", "signature_secret": "<secret>" }`. Returns `{ "id": "<uuid>" }`.
