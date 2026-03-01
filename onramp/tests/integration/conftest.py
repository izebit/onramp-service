"""Integration test fixtures: PostgreSQL via Testcontainers."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    """Start a PostgreSQL container and yield its connection URL."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def integration_engine(postgres_url: str):
    """Create SQLAlchemy engine bound to the Testcontainers PostgreSQL."""
    return create_engine(postgres_url, pool_pre_ping=True)


@pytest.fixture(scope="session")
def integration_session_factory(integration_engine):
    """Session factory for the integration DB."""
    return sessionmaker(autocommit=False, autoflush=False, bind=integration_engine)


@pytest.fixture(scope="session")
def _integration_app(postgres_url: str):
    """Set DATABASE_URL to container and import app so db module uses PostgreSQL."""
    os.environ["DATABASE_URL"] = postgres_url
    from app.main import app  # noqa: E402

    return app


@pytest.fixture
def client(
    _integration_app,
    integration_engine,
    integration_session_factory: sessionmaker,
) -> Generator[TestClient, None, None]:
    """FastAPI test client with real PostgreSQL (Testcontainers). Overrides get_db."""
    from app.db import Base, get_db
    from app.models import Order  # noqa: F401 - register with Base

    Base.metadata.create_all(bind=integration_engine)

    def _get_db() -> Generator[Session, None, None]:
        db = integration_session_factory()
        try:
            yield db
        finally:
            db.close()

    _integration_app.dependency_overrides[get_db] = _get_db
    with TestClient(_integration_app) as c:
        yield c
    _integration_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=integration_engine)
