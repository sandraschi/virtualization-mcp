"""Main server implementation for virtualization-mcp v2."""
import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, List, Type

from fastmcp import FastMCP

from .config import ServerConfig, load_config
from .services.service_manager import ServiceManager
from .plugins.plugin_manager import PluginManager
from .services.vbox_service import VirtualBoxService
from .utils import get_platform, ensure_dir

logger = logging.getLogger(__name__)

class VirtualizationMCPServer:
    """Main server class for virtualization-mcp."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize the virtualization-mcp server.
        
        Args:
            config: Server configuration. If not provided, will load default config.
        """
        self.config = config or load_config()
        self.mcp: Optional[FastMCP] = None
        self.service_manager = ServiceManager()
        self.plugin_manager = PluginManager(self.config)
        self._shutdown_event = asyncio.Event()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging based on the server configuration."""
        log_level = logging.DEBUG if self.config.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        
        # Set log level for all our modules
        for logger_name in ['virtualization_mcp', 'virtualization_mcp.server_v2']:
            logging.getLogger(logger_name).setLevel(log_level)
    
    async def start(self) -> None:
        """Start the virtualization-mcp server."""
        try:
            logger.info("=" * 80)
            logger.info(f"Starting virtualization-mcp Server v{self.config.version}")
            logger.info(f"Platform: {get_platform()}")
            logger.info("=" * 80)
            
            # Initialize services
            await self._initialize_services()
            
            # Initialize plugins
            await self.plugin_manager.initialize()
            
            # Create MCP instance
            self.mcp = FastMCP(
                name="virtualization-mcp",
                version=self.config.version,
                description="VirtualBox Management and Control Protocol Server"
            )
            
            # Register tools from services and plugins
            await self._register_tools()
            
            # Set up signal handlers
            self._setup_signal_handlers()
            
            logger.info("virtualization-mcp server started successfully")
            logger.info("Press Ctrl+C to stop the server")
            
            # Run the MCP server
            await self.mcp.run(transport="stdio")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except asyncio.CancelledError:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.critical(f"Fatal error in virtualization-mcp server: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    async def _initialize_services(self) -> None:
        """Initialize all required services."""
        logger.info("Initializing services...")
        
        # Initialize VirtualBox service
        vbox_service = VirtualBoxService({
            'vbox_manage_path': self.config.vbox_manage_path,
            'default_vm_folder': self.config.default_vm_folder
        })
        await self.service_manager.register_service('vbox', vbox_service)
        
        # Ensure data directories exist
        ensure_dir(self.config.base_dir)
        ensure_dir(self.config.log_dir)
    
    async def _register_tools(self) -> None:
        """Register all tools with the MCP instance."""
        if not self.mcp:
            raise RuntimeError("MCP instance not initialized")
        
        logger.info("Registering tools...")
        
        # Register core tools
        self._register_core_tools()
        
        # Register plugin tools
        await self.plugin_manager.register_tools(self.mcp)
        
        logger.info(f"Registered {len(self.mcp._tools)} tools")
    
    def _register_core_tools(self) -> None:
        """Register core tools with the MCP instance."""
        if not self.mcp:
            return
        
        @self.mcp.tool(
            name="virtualization-mcp_ping",
            description="Check if the virtualization-mcp server is running",
            parameters={},
            returns={"type": "string"}
        )
        async def ping() -> str:
            """Return a pong message to verify the server is running."""
            return "pong"
        
        @self.mcp.tool(
            name="virtualization-mcp_shutdown",
            description="Shut down the virtualization-mcp server",
            parameters={},
            returns={"type": "string"}
        )
        async def shutdown_server() -> str:
            """Shut down the virtualization-mcp server."""
            logger.info("Received shutdown request via API")
            asyncio.create_task(self._graceful_shutdown())
            return "Shutting down virtualization-mcp server..."
        
        @self.mcp.tool(
            name="virtualization-mcp_list_tools",
            description="List all available tools",
            parameters={
                "include_docs": {
                    "type": "boolean",
                    "description": "Include tool documentation",
                    "required": False,
                    "default": False
                }
            },
            returns={"type": "object"}
        )
        async def list_tools(include_docs: bool = False) -> Dict[str, Any]:
            """List all available tools."""
            if not self.mcp:
                return {"error": "MCP instance not initialized"}
            
            tools = {}
            for name, tool in self.mcp._tools.items():
                tool_info = {
                    "name": name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }
                
                if include_docs:
                    tool_info["docstring"] = tool.get("function", {}).__doc__ or ""
                
                tools[name] = tool_info
            
            return {"tools": tools}
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._handle_shutdown_signal, sig)
    
    def _handle_shutdown_signal(self, signum: int) -> None:
        """Handle shutdown signals."""
        signame = signal.Signals(signum).name
        logger.info(f"Received signal {signame}, shutting down...")
        asyncio.create_task(self._graceful_shutdown())
    
    async def _graceful_shutdown(self) -> None:
        """Perform a graceful shutdown of the server."""
        if self._shutdown_event.is_set():
            return
            
        self._shutdown_event.set()
        
        # Stop the MCP server if it's running
        if self.mcp and hasattr(self.mcp, 'stop'):
            await self.mcp.stop()
    
    async def shutdown(self) -> None:
        """Shut down the server and all services."""
        if not hasattr(self, '_shutdown_complete') or self._shutdown_complete:
            return
            
        logger.info("Shutting down virtualization-mcp server...")
        
        # Shutdown plugins
        if hasattr(self, 'plugin_manager'):
            try:
                await self.plugin_manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugins: {e}", exc_info=True)
        
        # Shutdown services
        if hasattr(self, 'service_manager'):
            try:
                await self.service_manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down services: {e}", exc_info=True)
        
        logger.info("virtualization-mcp server shutdown complete")
        self._shutdown_complete = True


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
    except Exception as e:
        logging.critical(f"Fatal error in virtualization-mcp server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()



