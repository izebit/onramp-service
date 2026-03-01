"""FastAPI application entrypoint: runs migrations and orders CDC consumer."""

import asyncio
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import Settings
from app.listeners import run_orders_cdc_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

settings = Settings()


def _run_migrations() -> None:
    """Run Alembic migrations to head."""
    root = Path(__file__).resolve().parent.parent
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run migrations, start orders CDC consumer."""
    _run_migrations()
    consumer_task = asyncio.create_task(run_orders_cdc_consumer(settings))
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}
