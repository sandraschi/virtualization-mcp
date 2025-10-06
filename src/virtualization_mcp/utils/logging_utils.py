"""
Logging configuration and utilities for the VirtualBox MCP server.
"""

import logging
from typing import Optional

import logging.handlers
from pathlib import Path

def setup_logging(debug: bool = False, log_file: str = "logs/virtualization-mcp.log") -> None:
    """
    Configure logging with optional debug mode and file output.

    Args:
        debug: If True, sets log level to DEBUG. Otherwise, uses INFO.
        log_file: Path to the log file.
    """
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler
    log_file_path = Path(log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    logging.getLogger('fastmcp').setLevel(logging.WARNING if not debug else logging.DEBUG)
    logger.info("Logging configured to file: %s", log_file)



