"""Main entry point for the VBoxMCP server."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from .core.server import VBoxMCPServer
from .config import load_config

def main():
    """Main entry point for the VBoxMCP server."""
    try:
        # Load configuration
        config = load_config()
        
        # Create and start the server
        server = VBoxMCPServer(config)
        
        # Run the server
        asyncio.run(server.start())
        
    except KeyboardInterrupt:
        print("\nShutting down VBoxMCP server...")
        sys.exit(0)
    except Exception as e:
        logging.critical("Fatal error in VBoxMCP server: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
