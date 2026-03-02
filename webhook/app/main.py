"""FastAPI application entrypoint."""

import asyncio
import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import Settings
from app.listeners import run_orders_cdc_consumer
from app.sender import run_sender
from app.routers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start orders CDC consumer and sender, then serve."""
    consumer_task = asyncio.create_task(run_orders_cdc_consumer(settings))
    sender_task = asyncio.create_task(run_sender(settings))
    try:
        yield
    finally:
        consumer_task.cancel()
        sender_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        try:
            await sender_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}
