import asyncio
import signal
import sys
import time
from typing import Callable, Optional

from loguru import logger

_shutdown_handlers: list[Callable[[], None]] = []
_shutdown_timeout_seconds = 10
_shutdown_callback: Optional[Callable[[], None]] = None


def register_shutdown_handler(handler: Callable[[], None]) -> None:
    _shutdown_handlers.append(handler)


def set_shutdown_timeout(seconds: int) -> None:
    global _shutdown_timeout_seconds
    _shutdown_timeout_seconds = seconds


def set_shutdown_callback(callback: Callable[[], None]) -> None:
    global _shutdown_callback
    _shutdown_callback = callback


async def execute_shutdown_sequence() -> None:
    start_time = time.time()
    logger.bind(event="shutdown_start").info("Executing shutdown sequence")

    for handler in _shutdown_handlers:
        handler_name = getattr(handler, "__name__", str(handler))
        try:
            elapsed = time.time() - start_time
            logger.bind(
                event="shutdown_step", step=handler_name, elapsed_ms=f"{elapsed:.3f}"
            ).info(f"Executing: {handler_name}")

            if asyncio.iscoroutinefunction(handler):
                await asyncio.wait_for(handler(), timeout=_shutdown_timeout_seconds)
            else:
                handler()

            elapsed = time.time() - start_time
            logger.bind(
                event="shutdown_step_complete",
                step=handler_name,
                elapsed_ms=f"{elapsed:.3f}",
            ).info(f"Completed: {handler_name}")
        except asyncio.TimeoutError:
            logger.bind(event="shutdown_timeout", step=handler_name).error(
                f"Timeout ({_shutdown_timeout_seconds}s) exceeded for {handler_name}"
            )
        except Exception as e:
            logger.bind(event="shutdown_error", step=handler_name, error=str(e)).error(
                f"Error in {handler_name}: {e}"
            )

    total_elapsed = time.time() - start_time
    logger.bind(event="shutdown_complete", total_ms=f"{total_elapsed:.3f}").info(
        "Shutdown sequence complete"
    )


def _sync_shutdown_handler(signum: int, frame) -> None:
    signal_name = signal.Signals(signum).name
    logger.bind(event="shutdown_signal", signal=signal_name).info(
        f"Received {signal_name}, initiating graceful shutdown"
    )

    if _shutdown_callback:
        try:
            _shutdown_callback()
        except Exception as e:
            logger.bind(event="shutdown_callback_error", error=str(e)).error(
                f"Error in shutdown callback: {e}"
            )

    sys.exit(0 if signum == signal.SIGTERM else 1)


def setup_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _sync_shutdown_handler)
    signal.signal(signal.SIGINT, _sync_shutdown_handler)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, _sync_shutdown_handler)

    logger.bind(event="signal_handlers_initialized").info(
        "Signal handlers registered: SIGTERM, SIGINT"
        + (", SIGHUP" if sys.platform != "win32" else "")
    )

    start_time = time.time()

    async def run_with_timeout(coro, name: str) -> bool:
        try:
            await asyncio.wait_for(coro, timeout=_shutdown_timeout_seconds)
            elapsed = time.time() - start_time
            logger.bind(
                event="shutdown_step", step=name, elapsed_ms=f"{elapsed:.3f}"
            ).info(f"Completed: {name}")
            return True
        except asyncio.TimeoutError:
            logger.bind(event="shutdown_timeout", step=name).error(
                f"Timeout ({_shutdown_timeout_seconds}s) exceeded for {name}"
            )
            return False

    for handler in _shutdown_handlers:
        handler_name = getattr(handler, "__name__", str(handler))
        try:
            if asyncio.iscoroutinefunction(handler):
                await run_with_timeout(handler(), handler_name)
            else:
                handler()
                elapsed = time.time() - start_time
                logger.bind(
                    event="shutdown_step",
                    step=handler_name,
                    elapsed_ms=f"{elapsed:.3f}",
                ).info(f"Completed: {handler_name}")
        except Exception as e:
            logger.bind(event="shutdown_error", step=handler_name, error=str(e)).error(
                f"Error in {handler_name}: {e}"
            )

    total_elapsed = time.time() - start_time
    logger.bind(event="shutdown_complete", total_ms=f"{total_elapsed:.3f}").info(
        "Shutdown sequence complete"
    )

    sys.exit(0 if signum == signal.SIGTERM else 1)


def setup_signal_handlers() -> None:
    loop = asyncio.get_event_loop()

    def sync_shutdown_handler(signum, frame):
        asyncio.create_task(graceful_shutdown(signum, frame))

    signal.signal(signal.SIGTERM, sync_shutdown_handler)
    signal.signal(signal.SIGINT, sync_shutdown_handler)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, sync_shutdown_handler)

    logger.bind(event="signal_handlers_initialized").info(
        "Signal handlers registered: SIGTERM, SIGINT"
        + (", SIGHUP" if sys.platform != "win32" else "")
    )
