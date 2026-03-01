"""FastAPI application entrypoint."""

import logging
import sys

from fastapi import FastAPI

from app.config import Settings
from app.routers import quotes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

settings = Settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(quotes.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}
