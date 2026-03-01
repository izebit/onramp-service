"""Root pytest configuration. No app import here so unit/integration can set DB per suite."""

import inspect
import os

# Use inspect.iscoroutinefunction so code (e.g. FastAPI) that still calls
# asyncio.iscoroutinefunction uses the non-deprecated API (Python 3.14+).
import asyncio

asyncio.iscoroutinefunction = inspect.iscoroutinefunction  # type: ignore[assignment]

# Use a 32+ byte secret in tests to avoid PyJWT InsecureKeyLengthWarning (RFC 7518).
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
