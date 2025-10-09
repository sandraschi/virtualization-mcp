"""
Run the virtualization-mcp server with proper Python path and error handling.
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('virtualization_mcp.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def run_server():
    """Run the virtualization-mcp server."""
    try:
        from virtualization_mcp.all_tools_server import start_mcp_server
        logger.info("Starting virtualization-mcp server...")
        server = await start_mcp_server(host="0.0.0.0", port=8000)
        logger.info("virtualization-mcp server started successfully")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
            
    except ImportError as e:
        logger.error(f"Failed to import virtualization-mcp: {e}")
        logger.error("Make sure all dependencies are installed and the module is in the Python path.")
        logger.error(f"Python path: {sys.path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running virtualization-mcp server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info("=== Starting virtualization-mcp Server ===")
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Shutting down virtualization-mcp server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)



