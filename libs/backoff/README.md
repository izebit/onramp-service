# backoff

Shared retry delay: exponential backoff with full jitter. Used by executor (invoker) and webhook (sender).

- `retry_delay_seconds(attempt_index: int) -> float` — delay in seconds for attempt index (0 = first retry).
