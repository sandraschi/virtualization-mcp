#!/usr/bin/env python3
"""
VirtualBox MCP Server - FastMCP 2.11.0 Implementation

Main entry point for the VirtualBox MCP server.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Import local modules
from .utils.logging_utils import setup_logging
from .utils.signal_handlers import register_signal_handlers
from .config import DEBUG, LOG_LEVEL

# Set up logging
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="VirtualBox MCP Server")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=DEBUG,
        help="Enable debug logging"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on"
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the VirtualBox MCP server."""
    args = parse_arguments()
    
    # Configure logging
    setup_logging(debug=args.debug)
    logger.info("Starting VirtualBox MCP Server")
    
    # Register signal handlers for graceful shutdown
    register_signal_handlers()
    
    try:
        # Initialize FastMCP first to avoid circular imports
        from fastmcp import FastMCP
        mcp = FastMCP(
            name="vboxmcp",
            version="2.11.0"
        )
        
        # Initialize services after FastMCP is created
        from .services.service_manager import service_manager
        try:
            logger.info("Initializing services...")
            service_manager.initialize_services()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise
        
        # Import and register API routes and tools
        try:
            from .api import register_routes
            from .mcp_tools import register_mcp_tools
            
            # Register MCP tools
            logger.info("Registering MCP tools...")
            register_mcp_tools(mcp)
            
            # Register API routes
            logger.info("Registering API routes...")
            register_routes(mcp)
            
            # Verify tools are registered
            if hasattr(mcp, '_tools') and mcp._tools:
                logger.info(f"Registered {len(mcp._tools)} tools: {list(mcp._tools.keys())}")
            else:
                logger.warning("No tools were registered with the MCP server")
                
        except ImportError as e:
            logger.error(f"Failed to import and register components: {e}", exc_info=True)
            raise
        
        # Start the server with stdio communication
        logger.info("Starting MCP server with stdio communication...")
        import asyncio
        asyncio.run(mcp.run_stdio_async(show_banner=False))
        
    except ImportError as e:
        logger.error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
