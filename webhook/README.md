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
- `KAFKA_BOOTSTRAP_SERVERS` — Kafka brokers (default `localhost:9092`)
- `KAFKA_ORDERS_TOPIC` — Debezium CDC topic for orders (default `dbserver1.public.orders`)
- `KAFKA_CONSUMER_GROUP` — consumer group id (default `webhook-orders-consumer`)

## Orders CDC listener

On startup, a background consumer subscribes to the orders Debezium CDC Kafka topic. For each event (create/update/delete), it looks up webhooks by `client_ref` and POSTs the CDC envelope to each URL with header `X-Webhook-Signature` (HMAC-SHA256 of the JSON body using the webhook’s `signature_secret`).

## Endpoints

- `POST /api/v1/clients/webhooks` — register webhook URL (requires `Authorization: Bearer <JWT>`). Body: `{ "url": "https://...", "signature_secret": "<secret>" }`. Returns `{ "id": "<uuid>" }`.
