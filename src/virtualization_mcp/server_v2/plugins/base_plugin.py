"""Base plugin implementation for VBoxMCP."""
from typing import Dict, Any, Optional
from fastmcp import FastMCP

class BasePlugin:
    """Base class for all VBoxMCP plugins.
    
    Plugins should inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the plugin with its configuration.
        
        Args:
            config: Plugin-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__.lower().replace('plugin', '')
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the plugin.
        
        This method should be overridden by plugin implementations to perform
        any necessary initialization.
        """
        if self._initialized:
            return
            
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shut down the plugin.
        
        This method should be overridden by plugin implementations to perform
        any necessary cleanup.
        """
        if not self._initialized:
            return
            
        self._initialized = False
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register tools provided by this plugin with the MCP instance.
        
        Args:
            mcp: The MCP instance to register tools with
        """
        pass
