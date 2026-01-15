"""
Web server launcher for virtualization-mcp.

Runs the FastAPI web server on HTTP transport, separate from the MCP server.
"""

import logging
import os
import sys
from pathlib import Path

import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from virtualization_mcp.config import configure_logging, settings
from virtualization_mcp.web.app import app

logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI web server."""
    configure_logging()

    port = int(os.getenv("WEB_PORT", settings.WEB_PORT if hasattr(settings, "WEB_PORT") else 3080))
    host = os.getenv("WEB_HOST", "0.0.0.0")

    logger.info(f"Starting FastAPI web server on http://{host}:{port}")
    logger.info(f"Web interface: http://localhost:{port}")
    logger.info(f"API docs: http://localhost:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()

