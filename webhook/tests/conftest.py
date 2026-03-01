"""Root pytest configuration."""

import inspect
import os

import asyncio

# Use non-deprecated inspect.iscoroutinefunction when code calls asyncio.iscoroutinefunction.
asyncio.iscoroutinefunction = inspect.iscoroutinefunction  # type: ignore[assignment]

os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
