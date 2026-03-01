# Executor

Service that executes orders. It consumes order CDC events from Kafka and enqueues new orders into `order_processing_steps` for execution.

## Table: order_processing_steps

| Column         | Type      | Description                    |
|----------------|-----------|--------------------------------|
| id             | serial PK |                                |
| order_id       | string    | Order ID from CDC              |
| status         | enum      | PENDING, COMPLETED, FAILED     |
| retry          | int       | Default 0                      |
| process_after  | timestamptz | When to process (default now) |
| created_at     | timestamptz | Row creation time             |

On each **create** (op `c`) event for the orders topic, one row is inserted with `order_id` from the event, `status=PENDING`, `retry=0`, `process_after=now()`.

## Run

```bash
cd executor
cp .env.example .env   # set DATABASE_URL, KAFKA_* as needed
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8002
```

Migrations run on startup. The order CDC consumer runs in the app lifespan and enqueues new orders for execution.
