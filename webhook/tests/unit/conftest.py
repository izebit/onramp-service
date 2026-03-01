"""Unit test fixtures: SQLite in-memory."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db import engine
from app.main import app

from tests.run_alembic import run_upgrade


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with SQLite in-memory DB."""
    conn = engine.connect()
    try:
        run_upgrade("head", connection=conn)
        with TestClient(app) as c:
            yield c
    finally:
        conn.close()
