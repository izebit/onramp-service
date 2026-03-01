"""Integration test fixtures: PostgreSQL via Testcontainers."""

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from tests.run_alembic import run_upgrade


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    """Start a PostgreSQL container and yield its connection URL."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def _integration_db_env(postgres_url: str) -> str:
    """Set DATABASE_URL so app.db and migrations use the container. Must run before any app import."""
    os.environ["DATABASE_URL"] = postgres_url
    return postgres_url


@pytest.fixture(scope="session")
def _ensure_db_env(_integration_db_env: str) -> str:
    """Dependency for fixtures that need DATABASE_URL set (e.g. settings). No-op, just forces order."""
    return _integration_db_env


@pytest.fixture(scope="session")
def integration_engine(_integration_db_env: str):
    """Create engine and run Alembic migrations on the container."""
    engine = create_engine(_integration_db_env, pool_pre_ping=True)
    with engine.connect() as conn:
        run_upgrade("head", connection=conn)
    return engine


@pytest.fixture(scope="session")
def integration_session_factory(integration_engine):
    """Session factory for querying the integration DB."""
    return sessionmaker(autocommit=False, autoflush=False, bind=integration_engine)


@pytest.fixture
def settings(_ensure_db_env):
    """Settings using container DATABASE_URL. Use so env is set before any test imports app."""
    from app.config import Settings
    return Settings()


@pytest.fixture
def _patch_app_db(integration_engine):
    """Patch app.db.SessionLocal to use the container engine so process_cdc_envelope writes to Postgres."""
    import app.db as db_module
    original = db_module.SessionLocal
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=integration_engine)
    try:
        yield
    finally:
        db_module.SessionLocal = original


@pytest.fixture
def db_session(
    integration_session_factory: sessionmaker,
    _patch_app_db,
) -> Generator[Session, None, None]:
    """Per-test session for assertions. Patches app.db so listener uses same DB."""
    session = integration_session_factory()
    try:
        yield session
    finally:
        session.close()
