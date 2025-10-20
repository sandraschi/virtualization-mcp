"""
Service Manager for virtualization-mcp

Handles initialization and management of all services and their dependencies.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages initialization and access to all services in the application."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._services: dict[str, Any] = {}
            self._initialized = True

    def initialize_services(self, config: dict | None = None) -> None:
        """Initialize all services with the given configuration."""
        if not self._services:
            logger.info("Initializing services...")

            # Initialize configuration first
            from .. import config as app_config

            # Create a config dictionary from the module's attributes
            loaded_config = {
                key: getattr(app_config, key)
                for key in dir(app_config)
                if not key.startswith("__") and not callable(getattr(app_config, key))
            }
            self._services["config"] = config or loaded_config

            # Initialize VBoxManager with lazy imports
            try:
                from ..vbox.manager import VBoxManager

                # Get the VBoxManage path from config or use default
                try:
                    from ..config import get_vbox_manage_path

                    vboxmanage_path = get_vbox_manage_path()
                    logger.info(f"Using VBoxManage path: {vboxmanage_path}")
                    self._services["vbox_manager"] = VBoxManager(
                        vboxmanage_path=str(vboxmanage_path)
                    )
                except Exception as e:
                    logger.warning(f"Failed to get VBoxManage path, using default: {e}")
                    self._services["vbox_manager"] = VBoxManager()

                # Initialize VM Operations
                from ..vbox.vm_operations import VMOperations

                self._services["vm_operations"] = VMOperations(self._services["vbox_manager"])

                # Initialize VM Service
                from .vm_service import VMService

                self._services["vm_service"] = VMService()

            except ImportError as e:
                logger.error(f"Failed to initialize services: {e}", exc_info=True)
                raise

            logger.info("All services initialized successfully")

    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        return self._services[service_name]

    @property
    def vm_service(self):
        """Get the VM service."""
        return self.get_service("vm_service")

    @property
    def vbox_manager(self):
        """Get the VBox manager instance."""
        return self.get_service("vbox_manager")

    @property
    def config(self):
        """Get the configuration."""
        return self.get_service("config")


# Global service manager instance
service_manager = ServiceManager()


def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    return service_manager


__all__ = ["ServiceManager", "get_service_manager", "service_manager"]
