"""Core server implementation for the VBoxMCP server."""
import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, List, Type

from fastmcp import FastMCP

from ...services.service_manager import ServiceManager
from ...plugins.plugin_manager import PluginManager
from ...config import ServerConfig

logger = logging.getLogger(__name__)

class VBoxMCPServer:
    """Main server class for VBoxMCP."""
    
    def __init__(self, config: ServerConfig):
        """Initialize the VBoxMCP server.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.mcp: Optional[FastMCP] = None
        self.service_manager = ServiceManager()
        self.plugin_manager = PluginManager(config.plugins)
        self._shutdown_event = asyncio.Event()
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on the server configuration."""
        log_level = logging.DEBUG if self.config.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
    
    async def start(self):
        """Start the MCP server and all services."""
        try:
            logger.info("Starting VBoxMCP server...")
            
            # Initialize services
            await self._initialize_services()
            
            # Initialize plugins
            await self._initialize_plugins()
            
            # Create and configure MCP instance
            self.mcp = FastMCP(
                name="vboxmcp",
                version="2.11.2",
                description="VirtualBox Management and Control Protocol Server"
            )
            
            # Register tools
            await self._register_tools()
            
            # Set up signal handlers
            self._setup_signal_handlers()
            
            logger.info("VBoxMCP server started successfully")
            
            # Run the MCP server
            await self.mcp.run(transport="stdio")
            
        except Exception as e:
            logger.critical("Failed to start VBoxMCP server: %s", str(e), exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    async def _initialize_services(self):
        """Initialize all required services."""
        logger.info("Initializing services...")
        # TODO: Initialize services
        pass
    
    async def _initialize_plugins(self):
        """Initialize all configured plugins."""
        logger.info("Initializing plugins...")
        await self.plugin_manager.initialize()
    
    async def _register_tools(self):
        """Register all tools with the MCP instance."""
        if not self.mcp:
            raise RuntimeError("MCP instance not initialized")
        
        logger.info("Registering tools...")
        # TODO: Register tools from services and plugins
        
        # Register help tool last to include all other tools
        from ...tools.help_tool import HelpTool
        help_tool = HelpTool(self.mcp)
        help_tool.register()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, self._handle_shutdown_signal)
    
    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signal.Signals(signum).name}, shutting down...")
        self._shutdown_event.set()
    
    async def shutdown(self):
        """Shut down the server and all services."""
        logger.info("Shutting down VBoxMCP server...")
        
        # Shutdown plugins
        if hasattr(self, 'plugin_manager'):
            await self.plugin_manager.shutdown()
        
        # Shutdown services
        if hasattr(self, 'service_manager'):
            await self.service_manager.shutdown()
        
        logger.info("VBoxMCP server shutdown complete")
