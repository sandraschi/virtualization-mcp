"""Example plugin for the VBoxMCP server."""
import logging
from typing import Dict, Any

from fastmcp import FastMCP
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class ExamplePlugin(BasePlugin):
    """An example plugin that demonstrates the plugin system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the example plugin."""
        super().__init__(config)
        self.counter = 0
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        await super().initialize()
        logger.info(f"ExamplePlugin initialized with config: {self.config}")
    
    async def shutdown(self) -> None:
        """Shut down the plugin."""
        await super().shutdown()
        logger.info("ExamplePlugin shut down")
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register example tools with the MCP instance."""
        
        @mcp.tool(
            name="example_hello",
            description="A simple example tool that says hello",
            parameters={
                "name": {
                    "type": "string",
                    "description": "Name to say hello to",
                    "required": True
                }
            },
            returns={"type": "string"}
        )
        async def hello(name: str) -> str:
            """Say hello to someone."""
            return f"Hello, {name}! This is the ExamplePlugin saying hi!"
        
        @mcp.tool(
            name="example_counter",
            description="A simple counter that increments on each call"
        )
        async def counter() -> Dict[str, int]:
            """Get the current counter value and increment it."""
            self.counter += 1
            return {"count": self.counter}
        
        logger.info("Registered example tools")
