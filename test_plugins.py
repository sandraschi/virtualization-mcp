#!/usr/bin/env python3
"""
Test script to verify Hyper-V and Windows Sandbox plugins.
"""
import asyncio
import logging
import os
import platform
import sys
import traceback
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Tuple

# Add parent directory to Python path
root_dir = Path(__file__).parent.resolve()
src_dir = root_dir / 'src'
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(root_dir))

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Print environment info
logger.info("=" * 80)
logger.info(f"Python: {sys.version}")
logger.info(f"Platform: {platform.platform()}")
logger.info(f"Working Directory: {os.getcwd()}")
logger.info(f"Python Path: {sys.path}")
logger.info("=" * 80)

def import_module_safe(module_name: str):
    """Safely import a module with detailed error reporting."""
    try:
        logger.debug(f"Attempting to import {module_name}")
        module = importlib.import_module(module_name)
        logger.info(f"✅ Successfully imported {module_name}")
        return module
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        logger.debug(f"Import error details: {traceback.format_exc()}")
        raise

# Import core modules
try:
    # Try to import FastMCP
    FastMCP = import_module_safe('fastmcp').FastMCP
    
    # Import virtualization-mcp modules
    virtualization-mcp = import_module_safe('virtualization-mcp')
    settings = import_module_safe('virtualization-mcp.config').settings
    plugins = import_module_safe('virtualization-mcp.plugins')
    
    # Get plugin components
    initialize_plugins = getattr(plugins, 'initialize_plugins', None)
    get_hyperv_manager = getattr(plugins, 'get_hyperv_manager', None)
    get_windows_sandbox = getattr(plugins, 'get_windows_sandbox', None)
    PLUGINS_AVAILABLE = getattr(plugins, 'PLUGINS_AVAILABLE', False)
    
    # Import register_tools
    register_tools = import_module_safe('virtualization-mcp.tools.register_tools')
    register_all_tools = getattr(register_tools, 'register_all_tools', None)
    
    # Enable debug logging for tests
    settings.DEBUG = True
    
    # Log plugin availability
    logger.info(f"Plugins available: {PLUGINS_AVAILABLE}")
    
    # List all available modules in virtualization-mcp
    logger.info("Available modules in virtualization-mcp:")
    for name, obj in inspect.getmembers(virtualization-mcp):
        if not name.startswith('_'):
            logger.info(f"  - {name}: {type(obj).__name__}")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize test environment: {e}")
    logger.debug(f"Initialization error details: {traceback.format_exc()}")
    sys.exit(1)

class PluginTestResult:
    """Container for test results."""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: Optional[str] = None
        self.details: Dict[str, Any] = {}
    
    def fail(self, message: str, **details):
        """Mark test as failed with error message and details."""
        self.passed = False
        self.error = message
        self.details.update(details)
        logger.error(f"❌ {self.name} failed: {message}")
    
    def success(self, **details):
        """Mark test as passed with optional details."""
        self.passed = True
        self.details.update(details)
        logger.info(f"✅ {self.name} passed")

async def test_plugin_import() -> PluginTestResult:
    """Test that plugins can be imported."""
    result = PluginTestResult("Plugin Import Test")
    
    if not PLUGINS_AVAILABLE:
        result.fail("Plugins are not available on this platform")
        return result
    
    try:
        from virtualization-mcp.plugins.hyperv.manager import HyperVManagerPlugin
        from virtualization-mcp.plugins.sandbox.manager import WindowsSandboxHelper
        result.success(imported_plugins=["HyperVManagerPlugin", "WindowsSandboxHelper"])
    except ImportError as e:
        result.fail(f"Failed to import plugins: {e}", error_type=type(e).__name__)
        logger.debug("Import error traceback:", exc_info=True)
    
    return result

async def test_plugin_initialization() -> PluginTestResult:
    """Test that plugins can be initialized."""
    result = PluginTestResult("Plugin Initialization Test")
    
    if not PLUGINS_AVAILABLE:
        result.fail("Plugins are not available on this platform")
        return result
    
    try:
        # Initialize MCP server
        mcp = FastMCP(
            name="VBoxMCP Test",
            version="1.0.0",
            description="Test MCP server for VBoxMCP plugins"
        )
        
        # Register tools
        register_all_tools(mcp)
        
        # Initialize plugins
        success = await initialize_plugins(mcp)
        
        if not success:
            result.fail("Failed to initialize plugins")
            return result
        
        # Verify plugin instances
        hyperv = get_hyperv_manager()
        sandbox = get_windows_sandbox()
        
        if not hyperv or not sandbox:
            result.fail("Failed to get plugin instances", 
                       hyperv_available=hyperv is not None,
                       sandbox_available=sandbox is not None)
            return result
        
        # Verify tools are registered
        tools = mcp.get_tools()
        tool_names = [tool.name for tool in tools]
        
        # Check for expected tools
        expected_tools = [
            'list_hyperv_vms',
            'create_hyperv_vm',
            'create_sandbox_config'
        ]
        
        missing_tools = [t for t in expected_tools if t not in tool_names]
        
        if missing_tools:
            result.fail("Some expected tools are missing",
                       missing_tools=missing_tools,
                       available_tools=tool_names)
        else:
            result.success(available_tools=tool_names)
        
    except Exception as e:
        result.fail(f"Unexpected error: {e}", 
                   error_type=type(e).__name__,
                   traceback=traceback.format_exc())
    
    return result

async def run_tests() -> bool:
    """Run all tests and return overall success status."""
    if platform.system() != 'Windows':
        logger.error("❌ This test requires Windows platform")
        return False
    
    logger.info("=" * 80)
    logger.info("Starting VBoxMCP Plugin Tests")
    logger.info("=" * 80)
    
    tests = [
        test_plugin_import,
        test_plugin_initialization,
    ]
    
    results = []
    
    for test_func in tests:
        logger.info(f"\nRunning test: {test_func.__name__}")
        result = await test_func()
        results.append(result)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary:")
    logger.info("=" * 80)
    
    all_passed = all(r.passed for r in results)
    
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        logger.info(f"{status} - {result.name}")
        if not result.passed and result.error:
            logger.error(f"  Error: {result.error}")
            if result.details:
                logger.error("  Details:")
                for k, v in result.details.items():
                    logger.error(f"    {k}: {v}")
    
    logger.info("\nOverall Status: " + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
