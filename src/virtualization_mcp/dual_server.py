"""
Dual server launcher for virtualization-mcp.

Runs both FastMCP (stdio) and FastAPI (HTTP) servers concurrently.
Both servers share the same backend services.
"""

import asyncio
import logging
import multiprocessing
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from virtualization_mcp.config import configure_logging, settings

logger = logging.getLogger(__name__)


def run_mcp_server():
    """Run the FastMCP server (stdio transport)."""
    from virtualization_mcp.all_tools_server import start_mcp_server

    configure_logging()
    logger.info("Starting FastMCP server (stdio transport)...")
    
    try:
        mcp = start_mcp_server()
        logger.info("FastMCP server started successfully")
        # FastMCP runs in stdio mode, so this will block
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}", exc_info=True)
        sys.exit(1)


def run_web_server():
    """Run the FastAPI web server (HTTP transport)."""
    import uvicorn
    from virtualization_mcp.web.app import app

    configure_logging()
    
    port = int(os.getenv("WEB_PORT", getattr(settings, "WEB_PORT", 3080)))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    
    logger.info(f"Starting FastAPI web server on http://{host}:{port}")
    logger.info(f"Web interface: http://localhost:{port}")
    logger.info(f"API docs: http://localhost:{port}/docs")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
    except Exception as e:
        logger.error(f"Error running web server: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Run both servers in separate processes."""
    configure_logging()
    
    mode = os.getenv("SERVER_MODE", "mcp").lower()
    
    if mode == "mcp":
        # Run only MCP server (for Claude Desktop)
        logger.info("Running in MCP-only mode (stdio)")
        run_mcp_server()
    elif mode == "web":
        # Run only web server
        logger.info("Running in Web-only mode (HTTP)")
        run_web_server()
    elif mode == "dual":
        # Run both servers in separate processes
        logger.info("Running in dual mode (MCP + Web)")
        
        mcp_process = multiprocessing.Process(target=run_mcp_server, name="MCP-Server")
        web_process = multiprocessing.Process(target=run_web_server, name="Web-Server")
        
        mcp_process.start()
        web_process.start()
        
        try:
            # Wait for both processes
            mcp_process.join()
            web_process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down servers...")
            mcp_process.terminate()
            web_process.terminate()
            mcp_process.join()
            web_process.join()
    else:
        logger.error(f"Invalid SERVER_MODE: {mode}. Use 'mcp', 'web', or 'dual'")
        sys.exit(1)


if __name__ == "__main__":
    main()



