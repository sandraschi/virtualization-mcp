"""Base classes for virtualization-mcp plugins."""

from abc import ABC, abstractmethod
from typing import Any

from fastapi import APIRouter


class BasePlugin(ABC):
    """Base class for all virtualization-mcp plugins."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the plugin with configuration.

        Args:
            config: Plugin configuration from the main config file
        """
        self.config = config
        self.router = APIRouter()
        self.setup_routes()

    @abstractmethod
    def setup_routes(self) -> None:
        """Set up FastAPI routes for this plugin.

        This method should be implemented by subclasses to define their API endpoints.
        """
        pass

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this plugin.

        Returns:
            APIRouter: The FastAPI router with all plugin routes
        """
        return self.router

    async def startup(self) -> None:
        """Perform any startup tasks for the plugin.

        This method is called when the server starts up.
        """
        pass

    async def shutdown(self) -> None:
        """Perform any cleanup tasks for the plugin.

        This method is called when the server shuts down.
        """
        pass
