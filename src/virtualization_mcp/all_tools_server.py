#!/usr/bin/env python3
"""
virtualization-mcp - Main MCP Server Implementation

This is the main entry point for the virtualization-mcp server, which provides
a unified interface for managing VirtualBox VMs through MCP.
"""

import os
import sys

# Prevent multiple imports
if "virtualization-mcp_IMPORTED" not in os.environ:
    os.environ["virtualization-mcp_IMPORTED"] = "1"
    print("HELLO WORLD FROM virtualization-mcp SERVER!", file=sys.stderr)

import asyncio
import json
import logging
import signal
import sys
import traceback
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from fastmcp import FastMCP

try:
    # When running as a module
    from .json_encoder import VBoxJSONEncoder
    from .json_encoder import dumps as vbox_dumps
    from .json_encoder import loads as vbox_loads
except (ImportError, ModuleNotFoundError):
    # Fallback for direct script execution
    try:
        from json_encoder import VBoxJSONEncoder
        from json_encoder import dumps as vbox_dumps
        from json_encoder import loads as vbox_loads
    except ImportError:
        # Fallback for when json_encoder is not in path
        class VBoxJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                return str(obj)

        vbox_dumps = json.dumps
        vbox_loads = json.loads

# Add parent directory to path for module resolution
import sys

# Add parent directory to Python path for module resolution
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import our configuration
from virtualization_mcp.config import configure_logging, settings  # noqa: E402

# Create type aliases
T = TypeVar("T")
AsyncFunction = Callable[..., Awaitable[T]]

# Create an alias for backward compatibility
FastMCPServer = FastMCP

# Get logger
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received, stopping server...")
    shutdown_event.set()


# Register signal handlers
if sys.platform != "win32":
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

# Configure logging
configure_logging()

# Import all tool modules
try:
    # Handle both direct execution and module imports
    try:
        # First try absolute imports (for direct execution)
        from virtualization_mcp.tools.help_tool import help_command  # noqa: F401
        from virtualization_mcp.tools.network.network_tools import (  # noqa: F401
            create_hostonly_network,
            list_hostonly_networks,
            remove_hostonly_network,
        )
        from virtualization_mcp.tools.register_tools import register_all_tools
        from virtualization_mcp.tools.snapshot.snapshot_tools import (  # noqa: F401
            create_snapshot,
            delete_snapshot,
            list_snapshots,
            restore_snapshot,
        )
        from virtualization_mcp.tools.storage.storage_tools import (  # noqa: F401
            create_storage_controller,
            list_storage_controllers,
            remove_storage_controller,
        )
        from virtualization_mcp.tools.system.system_tools import (  # noqa: F401
            get_system_info,
            get_vbox_version,
            list_ostypes,
        )
        from virtualization_mcp.tools.vm.vm_tools import (  # noqa: F401
            clone_vm,
            create_vm,
            delete_vm,
            get_vm_info,
            list_vms,
            modify_vm,
            pause_vm,
            reset_vm,
            resume_vm,
            start_vm,
            stop_vm,
        )

        # Import plugins
        if sys.platform == "win32":
            try:
                from virtualization_mcp.plugins import initialize_plugins  # noqa: F401

                HYPERV_AVAILABLE = True
            except ImportError as e:
                logger.warning(f"Plugins not available: {e}")
                if settings.DEBUG:
                    logger.exception("Detailed import error:")
                HYPERV_AVAILABLE = False

    except ImportError:
        # Fall back to relative imports (for module import)
        from .tools.help_tool import help_command  # noqa: F401
        from .tools.network.network_tools import (  # noqa: F401
            create_hostonly_network,
            list_hostonly_networks,
            remove_hostonly_network,
        )
        from .tools.register_tools import register_all_tools
        from .tools.snapshot.snapshot_tools import (  # noqa: F401
            create_snapshot,
            delete_snapshot,
            list_snapshots,
            restore_snapshot,
        )
        from .tools.storage.storage_tools import (  # noqa: F401
            create_storage_controller,
            list_storage_controllers,
            remove_storage_controller,
        )
        from .tools.system.system_tools import (  # noqa: F401
            get_system_info,
            get_vbox_version,
            list_ostypes,
        )
        from .tools.vm.vm_tools import (  # noqa: F401
            clone_vm,
            create_vm,
            delete_vm,
            get_vm_info,
            list_vms,
            modify_vm,
            pause_vm,
            reset_vm,
            resume_vm,
            start_vm,
            stop_vm,
        )

        # Import plugins
        if sys.platform == "win32":
            try:
                from virtualization_mcp.plugins import initialize_plugins  # noqa: F401

                HYPERV_AVAILABLE = True
            except ImportError as e:
                logger.warning(f"Plugins not available: {e}")
                if settings.DEBUG:
                    logger.exception("Detailed import error:")
                HYPERV_AVAILABLE = False

    logger.info("Successfully imported all tool modules")

except ImportError as e:
    logger.error(f"Failed to import tool modules: {e}", exc_info=True)
    # Print the full path to help with debugging
    import sys

    logger.error(f"Python path: {sys.path}")
    raise


async def register_all_tools(mcp: FastMCP) -> None:
    """Register all available tools with the MCP server.

    Args:
        mcp: The FastMCP instance to register tools with.

    Raises:
        RuntimeError: If there's an error registering any tool.
    """
    from virtualization_mcp.tools.register_tools import register_all_tools as register_vbox_tools

    try:
        # Register virtualization-mcp tools based on TOOL_MODE setting
        tool_mode = getattr(settings, 'TOOL_MODE', 'production')
        register_vbox_tools(mcp, tool_mode=tool_mode)
        
        if tool_mode.lower() in ["testing", "all"]:
            logger.info(f"Registered ALL tools (portmanteau + individual) - {tool_mode} mode")
        else:
            logger.info(f"Registered portmanteau tools only - {tool_mode} mode")

        # Initialize plugins if available
        if sys.platform == "win32" and HYPERV_AVAILABLE:
            try:
                from virtualization_mcp.plugins import initialize_plugins

                await initialize_plugins(mcp)
                logger.info("Plugins initialized and tools registered")

            except Exception as e:
                error_msg = f"Failed to initialize plugins: {e}"
                logger.error(error_msg, exc_info=True)
                if settings.DEBUG:
                    logger.exception("Plugin initialization error:")

                # Only raise if in debug mode, otherwise continue without plugins
                if settings.DEBUG:
                    raise RuntimeError(error_msg) from e

        logger.info("All tools registered successfully with MCP server")

    except Exception as e:
        error_msg = f"Failed to register tools: {e}"
        logger.error(error_msg)
        if settings.DEBUG:
            logger.exception("Tool registration error:")
        raise RuntimeError(error_msg) from e


async def start_mcp_server(host: str = None, port: int = None) -> FastMCP:
    """Start the MCP server and register all tools.

    Args:
        host: Host to bind to. If None, uses value from settings.
        port: Port to listen on. If None, uses value from settings.

    Returns:
        The initialized FastMCP server instance.

    Raises:
        RuntimeError: If the server fails to start or register tools.
    """
    host = host or settings.HOST
    port = port or settings.PORT
    mcp = None

    try:
        logger.info(f"Initializing {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.debug(f"Using configuration: {settings.model_dump()}")

        # Initialize MCP server with settings
        mcp = FastMCPServer(
            name=settings.APP_NAME,
            version=settings.APP_VERSION,
            instructions="MCP server for VirtualBox management",
        )

        # Register all tools with timeout
        logger.info("Registering tools...")
        try:
            # First register all tools
            await register_all_tools(mcp)

            # Then initialize services that need async initialization
            from virtualization_mcp.tools.register_tools import initialize_services

            await asyncio.wait_for(initialize_services(), timeout=settings.VM_OPERATION_TIMEOUT)
        except asyncio.TimeoutError:
            raise RuntimeError("Tool registration and initialization timed out") from None

        # Start the server
        logger.info(f"Starting server on {host}:{port}")

        # FastMCP uses run() method, not start()
        # For MCP servers, we typically use stdio transport
        logger.info("Server initialized successfully")
        return mcp

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        if settings.DEBUG:
            logger.exception("Server startup error:")
        raise RuntimeError(f"Failed to start server: {e}") from e
    finally:
        logger.info("Server shutdown complete")


def main() -> int:
    """Main entry point for the MCP server.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    if sys.platform == "win32":
        # On Windows, add signal handlers
        def windows_signal_handler(sig):
            logger.info(f"Received Windows signal: {sig}")
            shutdown_event.set()
            return True  # Indicate we handled the signal

        import win32api

        # Set up the handler without keyword arguments
        win32api.SetConsoleCtrlHandler(windows_signal_handler, 1)  # 1 = add handler

    mcp = None
    try:
        # Initialize the MCP server synchronously
        mcp = asyncio.run(start_mcp_server())

        # Run the server with stdio transport (synchronous)
        logger.info("Server is running. Press Ctrl+C to stop.")
        mcp.run(transport="stdio")

        return 0

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        return 0

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        if settings.DEBUG:
            logger.exception("Error details:")
        return 1

    finally:
        logger.info("Server shutdown complete")


async def main_async():
    """Async entry point for the MCP server.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        # Initialize and start the MCP server
        server = await start_mcp_server()

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Clean up resources
        if server:
            await server.stop()

        logger.info("Server shutdown complete")
        return 0

    except Exception as e:
        logger.error(f"Error in main_async: {e}")
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
