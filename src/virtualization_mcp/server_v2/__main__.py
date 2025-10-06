"""Main entry point for the virtualization-mcp server."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from .core.server import virtualization-mcpServer
from .config import load_config

def main():
    """Main entry point for the virtualization-mcp server."""
    try:
        # Load configuration
        config = load_config()
        
        # Create and start the server
        server = virtualization-mcpServer(config)
        
        # Run the server
        asyncio.run(server.start())
        
    except KeyboardInterrupt:
        print("\nShutting down virtualization-mcp server...")
        sys.exit(0)
    except Exception as e:
        logging.critical("Fatal error in virtualization-mcp server: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()



