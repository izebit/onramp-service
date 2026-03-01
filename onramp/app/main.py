"""FastAPI application entrypoint."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.db import Base, engine
from app.listeners import run_order_tasks_cdc_consumer
from app.models import Order  # noqa: F401 - register model with Base
from app.routers import orders, quotes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup, start order_tasks CDC consumer when enabled."""
    Base.metadata.create_all(bind=engine)
    consumer_task = (
        asyncio.create_task(run_order_tasks_cdc_consumer(settings))
        if settings.enable_order_tasks_cdc
        else None
    )
    try:
        yield
    finally:
        if consumer_task is not None:
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

app.include_router(quotes.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}
