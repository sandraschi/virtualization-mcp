"""
Signal handling utilities for graceful shutdown.
"""

import logging
import signal
import sys
from typing import Any

logger = logging.getLogger(__name__)


def handle_shutdown(signum: int | None = None, frame: Any | None = None) -> None:
    """
    Handle shutdown signals gracefully.

    Args:
        signum: The signal number (optional).
        frame: The current stack frame (optional).
    """
    logger.info("Shutdown signal received, cleaning up...")
    # Just exit - FastMCP will handle cleanup
    sys.exit(0)


def register_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)


def setup_signal_handlers(loop=None, cleanup_callback=None):
    import signal
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))


def graceful_shutdown_handler(signum=None, frame=None):
    sys.exit(0)
