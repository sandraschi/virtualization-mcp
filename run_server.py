"""
Run the VBoxMCP server with enhanced error handling and logging.
"""

import asyncio
import logging
import sys
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
    """Run the VBoxMCP server."""
    try:
        from virtualization_mcp.all_tools_server import main
        logger.info("Successfully imported all_tools_server")
        await main()
    except ImportError as e:
        logger.error(f"Failed to import all_tools_server: {e}")
        logger.error("Please ensure all dependencies are installed and the module is in the Python path.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running VBoxMCP server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info("Starting VBoxMCP server...")
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Shutting down VBoxMCP server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
