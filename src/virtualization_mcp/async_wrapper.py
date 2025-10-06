#!/usr/bin/env python3
"""
Async wrapper for the existing virtualization-mcp server.

This module provides an async-compatible interface to the existing server implementation,
allowing it to work with FastMCP 2.10's stdio transport without major refactoring.
"""

import asyncio
import functools
import inspect
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('virtualization-mcp_async.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("virtualization-mcp_async")

# Type variables
T = TypeVar('T')
AsyncFunc = Callable[..., Any]

class AsyncWrapper:
    """Wraps synchronous functions to make them async-compatible."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the async wrapper.
        
        Args:
            max_workers: Maximum number of worker threads for sync operations
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        # Create a new event loop if one doesn't exist for the current thread
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:  # No event loop running for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
    async def run_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a synchronous function in a thread pool."""
        return await self.loop.run_in_executor(
            self.executor,
            functools.partial(func, *args, **kwargs)
        )
    
    def wrap(self, func: Callable) -> AsyncFunc:
        """Wrap a synchronous function to make it async."""
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            return await self.run_sync(func, *args, **kwargs)
        return wrapped

try:
    # Import FastMCP for the MCP server
    from fastmcp import FastMCP
    
    # Import the VM service
    from .services.vm_service import VMService
    
    # Initialize the VM service
    vm_service = VMService()
    
    # Create references to the service methods we want to expose
    create_vm = vm_service.create_vm
    start_vm = vm_service.start_vm
    stop_vm = vm_service.stop_vm
    delete_vm = vm_service.delete_vm
    get_vm_state = vm_service.get_vm_state
    
    # Get sandbox methods if available
    if hasattr(vm_service, 'create_sandbox'):
        create_sandbox = vm_service.create_sandbox
        reset_sandbox = vm_service.reset_sandbox
    else:
        # Provide stubs if sandbox functionality isn't available
        def sandbox_not_available(*args, **kwargs):
            raise NotImplementedError("Sandbox functionality is not available in this version")
        create_sandbox = sandbox_not_available
        reset_sandbox = sandbox_not_available
    
    # Get Hyper-V methods if available
    if hasattr(vm_service, 'enable_hyperv_integration'):
        enable_hyperv_integration = vm_service.enable_hyperv_integration
        create_hyperv_export = vm_service.create_hyperv_export
    else:
        # Provide stubs if Hyper-V functionality isn't available
        def hyperv_not_available(*args, **kwargs):
            raise NotImplementedError("Hyper-V functionality is not available in this version")
        enable_hyperv_integration = hyperv_not_available
        create_hyperv_export = hyperv_not_available
    
except ImportError as e:
    logger.critical("Failed to import required modules: %s", str(e))
    sys.exit(1)

# Initialize the async wrapper
wrapper = AsyncWrapper()

# Create async versions of all the functions
async_create_vm = wrapper.wrap(create_vm)
async_start_vm = wrapper.wrap(start_vm)
async_stop_vm = wrapper.wrap(stop_vm)
async_delete_vm = wrapper.wrap(delete_vm)
async_get_vm_state = wrapper.wrap(get_vm_state)
async_create_sandbox = wrapper.wrap(create_sandbox)
async_reset_sandbox = wrapper.wrap(reset_sandbox)
async_enable_hyperv_integration = wrapper.wrap(enable_hyperv_integration)
async_create_hyperv_export = wrapper.wrap(create_hyperv_export)

async def main() -> None:
    """Main async entry point for the virtualization-mcp server."""
    try:
        # Create FastMCP instance with stdio transport
        mcp = FastMCP(
            name="virtualization-mcp",
            version="1.0.0",
            transport='stdio',
            debug=True
        )
        
        # Register all the wrapped functions
        mcp.tool()(async_create_vm)
        mcp.tool()(async_start_vm)
        mcp.tool()(async_stop_vm)
        mcp.tool()(async_delete_vm)
        mcp.tool()(async_get_vm_state)
        mcp.tool()(async_create_sandbox)
        mcp.tool()(async_reset_sandbox)
        mcp.tool()(async_enable_hyperv_integration)
        mcp.tool()(async_create_hyperv_export)
        # Register all other wrapped functions...
        
        logger.info("virtualization-mcp async wrapper started with stdio transport")
        
        # Run the MCP server
        await mcp.run()
        
    except Exception as e:
        logger.critical("Fatal error in virtualization-mcp async wrapper: %s", str(e), exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down virtualization-mcp async wrapper")
    except Exception as e:
        logger.critical("Unhandled exception: %s", str(e), exc_info=True)
        sys.exit(1)



