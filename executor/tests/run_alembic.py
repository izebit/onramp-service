"""Run Alembic migrations from tests."""

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config


def _alembic_cfg(connection: Any = None) -> Config:
    root = Path(__file__).resolve().parent.parent
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def run_upgrade(revision: str = "head", connection: Any = None) -> None:
    """Run alembic upgrade."""
    command.upgrade(_alembic_cfg(connection=connection), revision)
