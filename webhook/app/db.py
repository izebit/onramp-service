"""Database connection and session."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings

settings = Settings()
_is_sqlite = "sqlite" in settings.database_url
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
_poolclass = StaticPool if _is_sqlite else None
engine = create_engine(
    settings.database_url,
    pool_pre_ping=(not _is_sqlite),
    connect_args=_connect_args,
    poolclass=_poolclass,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
