# onramp-service

Multi-service repository. Each service lives in its own subdirectory with its own Poetry project.

## Services

- **[onramp/](onramp/)** — FastAPI stub service (quotes, orders)
- **[webhook/](webhook/)** — Webhook registration (POST /api/v1/clients/webhooks, JWT, store client_ref + url)

To work on a service, `cd` into its directory and use Poetry from there (e.g. `poetry install`, `poetry run uvicorn ...`).
