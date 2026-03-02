"""FastAPI application entrypoint for executor (order execution service)."""

import asyncio
import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import Settings
from app.invoker import run_invoker
from app.listeners import run_orders_cdc_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

logger = logging.getLogger(__name__)
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start order CDC consumer and invoker (process tasks via payment provider)."""
    consumer_task = asyncio.create_task(run_orders_cdc_consumer(settings))
    invoker_task = asyncio.create_task(run_invoker(settings))
    logger.info("CDC consumer and invoker tasks started")
    try:
        yield
    finally:
        consumer_task.cancel()
        invoker_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        try:
            await invoker_task
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
    logger.info("Health check endpoint called")
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}
