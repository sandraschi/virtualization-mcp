"""
API endpoints and route registrations for the VirtualBox MCP server.

This module handles the registration of all API endpoints with proper error handling,
input validation, and rate limiting.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, Optional, TypeVar, cast

from fastmcp import FastMCP

from ..exceptions import RateLimitExceeded, ServiceUnavailable, ValidationError, VMError
from ..mcp_tools import register_mcp_tools
from ..services.service_manager import get_service_manager
from ..utils.rate_limiter import RateLimiter

# Import API modules
from . import documentation
from .documentation import register_documentation_routes

logger = logging.getLogger(__name__)

# Global rate limiter
rate_limiter = RateLimiter(
    max_calls=100,  # Max 100 calls
    period=60,  # per 60 seconds
    burst=20,  # Allow burst of 20 calls
)


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle common errors and return appropriate responses."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Check rate limits
            if not rate_limiter.allow_request():
                raise RateLimitExceeded("Rate limit exceeded. Please try again later.")

            # Execute the function
            return await func(*args, **kwargs)

        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return {"status": "error", "message": str(e), "code": 400}

        except RateLimitExceeded as e:
            retry_after = rate_limiter.time_until_next_window()
            logger.warning(f"Rate limit exceeded: {e}")
            return {"status": "error", "message": str(e), "retry_after": retry_after, "code": 429}

        except VMError as e:
            logger.error(f"VM operation failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "code": 500}

        except ServiceUnavailable as e:
            logger.error(f"Service unavailable: {e}")
            return {"status": "error", "message": str(e), "code": 503}

        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            return {"status": "error", "message": "Internal server error", "code": 500}

    return wrapper


def validate_input(schema: dict) -> Callable:
    """Decorator to validate input parameters against a schema."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from jsonschema import ValidationError as JsonValidationError
            from jsonschema import validate

            try:
                # Get the input data (assuming it's the first argument after self)
                input_data = kwargs if kwargs else (args[1] if len(args) > 1 else {})

                # Validate against the schema
                validate(instance=input_data, schema=schema)

                # Call the original function
                return await func(*args, **kwargs)

            except JsonValidationError as e:
                raise ValidationError(f"Invalid input: {e.message}") from e

        return wrapper

    return decorator


class APIRegistrar:
    """Handles registration of API endpoints with proper validation and error handling."""

    def __init__(self):
        self.service_manager = get_service_manager()
        self.vm_service = self.service_manager.vm_service

    def register_routes(self, mcp: FastMCP) -> None:
        """Register all API routes with the FastMCP instance."""
        try:
            # VM Lifecycle
            self._register_vm_lifecycle_routes(mcp)

            # VM Configuration
            self._register_vm_config_routes(mcp)

            # Snapshot Management
            self._register_snapshot_routes(mcp)

            # Storage Management
            self._register_storage_routes(mcp)

            # Network Management
            self._register_network_routes(mcp)

            # Device Management
            self._register_device_routes(mcp)

            # Templates
            self._register_template_routes(mcp)

            # Metrics and Monitoring
            self._register_metrics_routes(mcp)

            # Audio/Video Settings
            self._register_av_routes(mcp)

            logger.info("All API routes registered successfully")

        except Exception as e:
            logger.critical(f"Failed to register API routes: {e}", exc_info=True)
            raise

    def _register_vm_lifecycle_routes(self, mcp: FastMCP) -> None:
        """Register VM lifecycle related routes."""
        vm_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "template": {"type": "string", "default": "ubuntu-dev"},
                "memory_mb": {"type": "integer", "minimum": 512},
                "disk_gb": {"type": "integer", "minimum": 10},
            },
            "required": ["name"],
        }

        @mcp.tool()
        @validate_input(vm_schema)
        @handle_errors
        async def create_vm(params: dict) -> dict:
            return await self.vm_service.create_vm(**params)

        # Register other lifecycle methods...

    def _register_vm_config_routes(self, mcp: FastMCP) -> None:
        """Register VM configuration related routes."""
        pass  # Implementation omitted for brevity

    # Other route registration methods...


def register_routes(mcp: FastMCP) -> None:
    """Register all API routes with the FastMCP instance.

    This function registers:
    1. MCP tool discovery endpoints
    2. Documentation endpoints
    3. Core API routes

    Args:
        mcp: The FastMCP instance to register routes with.
    """
    logger.info("Registering API routes...")

    try:
        # Register MCP tool discovery endpoints (works over stdio)
        register_mcp_tools(mcp)

        # Register documentation routes (for HTTP/OpenAPI)
        register_documentation_routes(mcp)

        # Register core API routes
        registrar = APIRegistrar()
        registrar.register_routes(mcp)

        logger.info("API routes registered successfully")
    except Exception as e:
        logger.error(f"Failed to register API routes: {e}")


__all__ = ["register_routes"]
