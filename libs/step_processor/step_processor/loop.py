"""Async loop: run sync cycle in executor, sleep, repeat until cancelled."""

import asyncio
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


async def run_loop(
    cycle_fn: Callable[[], None],
    *,
    poll_interval: float = 1.0,
    log_name: str = "Processor",
) -> None:
    """Run cycle_fn in a thread, sleep poll_interval, repeat. Stops on CancelledError."""
    logger.info("%s starting", log_name)
    loop = asyncio.get_running_loop()
    try:
        while True:
            try:
                await loop.run_in_executor(None, cycle_fn)
            except Exception as e:
                logger.exception("%s cycle failed: %s", log_name, e)
            await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
        logger.info("%s cancelled", log_name)
    finally:
        logger.info("%s stopped", log_name)
