"""
Signal handling utilities for graceful shutdown.
"""

import signal
import sys
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def handle_shutdown(signum: Optional[int] = None, frame: Optional[Any] = None) -> None:
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
