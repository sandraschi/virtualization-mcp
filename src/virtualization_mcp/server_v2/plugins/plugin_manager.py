"""Plugin management for the VBoxMCP server."""
import importlib
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Type, Any, List, Optional, TypeVar, Generic, Type

from virtualization_mcp.server_v2.config import ServerConfig
from virtualization_mcp.services.service_manager import ServiceManager
from virtualization_mcp.server_v2.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PluginManager:
    """Manages the loading and lifecycle of VBoxMCP plugins."""
    
    def __init__(self, config: ServerConfig):
        """Initialize the plugin manager.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.plugins: Dict[str, BasePlugin] = {}
        self._service_manager = ServiceManager()
        logger.debug("PluginManager initialized")
    
    async def initialize(self) -> None:
        """Initialize all enabled plugins."""
        logger.info("Initializing plugins...")
        
        # Load built-in plugins
        self._load_builtin_plugins()
        
        # Initialize all plugins
        for name, plugin in self.plugins.items():
            try:
                await plugin.initialize()
                logger.info(f"Initialized plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{name}': {e}", exc_info=True)
    
    def _load_builtin_plugins(self) -> None:
        """Load built-in plugins from the plugins directory."""
        # The plugins directory is now in the Python path
        plugins_pkg = "virtualization_mcp.server_v2.plugins"
        plugins_path = Path(__file__).parent
        
        # Find all Python modules in the plugins directory
        for finder, name, _ in pkgutil.iter_modules([str(plugins_path)]):
            if name.startswith('_') or name in ('base_plugin', 'plugin_manager'):
                continue
                
            try:
                # Import the plugin module
                full_name = f"{plugins_pkg}.{name}"
                module = importlib.import_module(f"{plugins_pkg}.{name}")
                
                # Find all classes that inherit from BasePlugin
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BasePlugin) and 
                        obj != BasePlugin and 
                        obj.__module__ == module.__name__):
                        
                        # Create an instance of the plugin with its config
                        plugin_config = {}
                        if hasattr(self.config, 'plugins') and name in self.config.plugins:
                            plugin_config = self.config.plugins[name]
                        
                        plugin = obj(plugin_config)
                        self.plugins[plugin.name] = plugin
                        
                        # Register the plugin
                        self.plugins[name] = plugin
                        logger.debug(f"Loaded plugin: {name}")
                        
            except Exception as e:
                logger.error(f"Failed to load plugin '{name}': {e}", exc_info=True)
    
    async def register_tools(self, mcp) -> None:
        """Register tools from all plugins with the MCP instance.
        
        Args:
            mcp: The MCP instance to register tools with
        """
        for name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'register_tools') and callable(plugin.register_tools):
                    plugin.register_tools(mcp)
                    logger.info(f"Registered tools for plugin: {name}")
                else:
                    logger.debug(f"Plugin {name} has no tools to register")
            except Exception as e:
                logger.error(f"Failed to register tools for plugin '{name}': {e}")
                if self.config.debug:
                    logger.exception("Tool registration error")
    
    async def shutdown(self) -> None:
        """Shut down all plugins."""
        logger.info("Shutting down plugins...")
        
        # Shutdown plugins in reverse order of initialization
        for name, plugin in reversed(self.plugins.items()):
            try:
                await plugin.shutdown()
                logger.debug(f"Shut down plugin: {name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin '{name}': {e}", exc_info=True)
        
        self.plugins.clear()
        logger.info("All plugins shut down")
