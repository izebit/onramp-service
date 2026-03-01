# step-processor

Shared task loop and step result application. Used by executor (invoker) and webhook (sender).

- `run_loop(cycle_fn, poll_interval=1.0, log_name="Processor")` — async loop: run sync cycle in executor, sleep, repeat until cancelled.
- `apply_step_result(session, step, success, max_retry, completed_status, failed_status, create_next_step)` — mark step completed/failed; on failure create retry step with backoff when retry < max.
