-- Create executor database for Debezium connector (executor.order_tasks).
-- Runs on first Postgres container init only.
CREATE DATABASE executor;
