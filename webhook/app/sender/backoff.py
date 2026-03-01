"""Retry delay calculation with exponential backoff and jitter."""

import random

def retry_delay_seconds(attempt_index: int) -> float:
    """Exponential backoff for attempt index (0 = first retry), with full jitter in [0, delay]."""
    delay = 1.0 * (2 ** (attempt_index + 1))
    return random.uniform(0, delay)
