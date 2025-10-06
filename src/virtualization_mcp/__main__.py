"""
virtualization-mcp Entry Point - Fixed for Claude Desktop Compatibility

This module serves as the entry point when running 'python -m virtualization-mcp'.
It uses the all_tools_server implementation.
"""

import sys
import logging
import asyncio

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from .all_tools_server import main
    logger.info("Successfully imported all_tools_server")
except ImportError as e:
    logger.error(f"Failed to import all_tools_server: {e}")
    raise

if __name__ == "__main__":
    try:
        # Enable debug mode if --debug flag is passed
        if "--debug" in sys.argv:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        # Run the server (main is now synchronous)
        logger.info("Starting virtualization-mcp server...")
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Shutting down virtualization-mcp server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in virtualization-mcp server: {e}", exc_info=True)
        sys.exit(1)



