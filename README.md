# onramp-service

Multi-service repository. Each service lives in its own subdirectory with its own Poetry project.

## Shared module

- **[libs/authorization/](libs/authorization/)** — JWT authorization (Bearer token, `client_ref` + `expiration_at`). Reused by onramp and webhook. Install from a service with `poetry install` (path dependency).

## Services

- **[onramp/](onramp/)** — FastAPI stub service (quotes, orders)
- **[webhook/](webhook/)** — Webhook registration (POST /api/v1/clients/webhooks, JWT, store client_ref + url)

To work on a service, `cd` into its directory and use Poetry from there (e.g. `poetry install`, `poetry run uvicorn ...`).
