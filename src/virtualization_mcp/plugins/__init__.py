"""
VBoxMCP Plugins Package

This package contains all plugin modules for VBoxMCP.
"""
import logging
from typing import Optional, Type
from fastmcp import FastMCP

# Configure logger
logger = logging.getLogger(__name__)

# Import plugin classes
try:
    from .hyperv.manager import HyperVManagerPlugin
    from .sandbox.manager import WindowsSandboxHelper
    PLUGINS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failed to import plugins: {e}")
    PLUGINS_AVAILABLE = False
    # Create dummy classes for type checking
    class DummyPlugin:
        def __init__(self, *args, **kwargs):
            pass
        async def initialize(self, *args, **kwargs):
            pass
        def register_tools(self, *args, **kwargs):
            pass
    
    class HyperVManagerPlugin(DummyPlugin):
        pass
    
    class WindowsSandboxHelper(DummyPlugin):
        pass

__all__ = [
    'HyperVManagerPlugin',
    'WindowsSandboxHelper',
    'initialize_plugins',
    'get_hyperv_manager',
    'get_windows_sandbox',
    'PLUGINS_AVAILABLE'
]

# Plugin instances
_hyperv_manager = None
_windows_sandbox = None

async def initialize_plugins(mcp: FastMCP) -> bool:
    """Initialize all plugins.
    
    Args:
        mcp: The FastMCP instance to initialize plugins with.
        
    Returns:
        bool: True if all plugins were initialized successfully, False otherwise.
    """
    global _hyperv_manager, _windows_sandbox
    
    if not PLUGINS_AVAILABLE:
        logger.warning("Plugins not available, skipping initialization")
        return False
    
    if _hyperv_manager is not None and _windows_sandbox is not None:
        logger.debug("Plugins already initialized")
        return True
    
    try:
        logger.info("Initializing plugins...")
        
        # Initialize Hyper-V Manager
        _hyperv_manager = HyperVManagerPlugin()
        await _hyperv_manager.initialize(mcp)
        _hyperv_manager.register_tools(mcp)
        logger.info("Hyper-V Manager plugin initialized")
        
        # Initialize Windows Sandbox Helper
        _windows_sandbox = WindowsSandboxHelper()
        await _windows_sandbox.initialize(mcp)
        _windows_sandbox.register_tools(mcp)
        logger.info("Windows Sandbox Helper plugin initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize plugins: {e}", exc_info=True)
        # Clean up partially initialized plugins
        _hyperv_manager = None
        _windows_sandbox = None
        return False

def get_hyperv_manager() -> Optional[HyperVManagerPlugin]:
    """Get the Hyper-V manager plugin instance.
    
    Returns:
        Optional[HyperVManagerPlugin]: The Hyper-V manager instance, or None if not available.
    """
    return _hyperv_manager

def get_windows_sandbox() -> Optional[WindowsSandboxHelper]:
    """Get the Windows Sandbox helper instance.
    
    Returns:
        Optional[WindowsSandboxHelper]: The Windows Sandbox helper instance, or None if not available.
    """
    return _windows_sandbox
