"""Unit test fixtures: SQLite in-memory, no external services."""

import os

import pytest
from fastapi.testclient import TestClient

# Set SQLite before any app import so db module uses it
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db import Base, engine
from app.main import app
from app.models import Order  # noqa: F401 - register with Base before create_all


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with SQLite in-memory DB."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
