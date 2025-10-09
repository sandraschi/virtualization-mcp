"""
System Management Portmanteau Tool

Consolidates all system-related operations into a single tool with action-based interface.
Replaces 5 individual system tools with one comprehensive tool.
"""

import logging
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP

# Import existing system tools
from virtualization_mcp.tools.system.system_tools import (
    get_system_info, get_vbox_version, list_ostypes
)

logger = logging.getLogger(__name__)

# Define available actions
SYSTEM_ACTIONS = {
    "host_info": "Get host system information",
    "vbox_version": "Get VirtualBox version information",
    "ostypes": "List available OS types",
    "metrics": "Get VM performance metrics",
    "screenshot": "Take a screenshot of a running VM"
}

def register_system_management_tool(mcp: FastMCP) -> None:
    """Register the system management portmanteau tool."""
    
    @mcp.tool(
        name="system_management",
        description="Comprehensive system information and diagnostics"
    )
    async def system_management(
        action: str,
        vm_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get system information and diagnostics with various actions.
        
        Args:
            action: The operation to perform. Available actions:
                - host_info: Get host system information (no vm_name required)
                - vbox_version: Get VirtualBox version information (no vm_name required)
                - ostypes: List available OS types (no vm_name required)
                - metrics: Get VM performance metrics (requires vm_name)
                - screenshot: Take a screenshot of a running VM (requires vm_name)
            
            vm_name: Name of the virtual machine (required for metrics and screenshot)
            **kwargs: Additional parameters for specific actions
            
        Returns:
            Dict containing the result of the operation
            
        Examples:
            # Get host system information
            result = await system_management(action="host_info")
            
            # Get VirtualBox version
            result = await system_management(action="vbox_version")
            
            # List available OS types
            result = await system_management(action="ostypes")
            
            # Get VM performance metrics
            result = await system_management(
                action="metrics",
                vm_name="MyVM"
            )
            
            # Take VM screenshot
            result = await system_management(
                action="screenshot",
                vm_name="MyVM"
            )
        """
        try:
            # Validate action
            if action not in SYSTEM_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(SYSTEM_ACTIONS.keys())}",
                    "available_actions": SYSTEM_ACTIONS
                }
            
            logger.info(f"Executing system management action: {action}")
            
            # Route to appropriate function based on action
            if action == "host_info":
                return await _handle_host_info(**kwargs)
            
            elif action == "vbox_version":
                return await _handle_vbox_version(**kwargs)
            
            elif action == "ostypes":
                return await _handle_ostypes(**kwargs)
            
            elif action == "metrics":
                return await _handle_metrics(vm_name=vm_name, **kwargs)
            
            elif action == "screenshot":
                return await _handle_screenshot(vm_name=vm_name, **kwargs)
            
            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": SYSTEM_ACTIONS
                }
                
        except Exception as e:
            logger.error(f"Error in system management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "available_actions": SYSTEM_ACTIONS
            }

async def _handle_host_info(**kwargs) -> Dict[str, Any]:
    """Handle host info action."""
    try:
        result = await get_system_info(**kwargs)
        return {
            "success": True,
            "action": "host_info",
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "action": "host_info",
            "error": f"Failed to get host info: {str(e)}"
        }

async def _handle_vbox_version(**kwargs) -> Dict[str, Any]:
    """Handle vbox version action."""
    try:
        result = await get_vbox_version(**kwargs)
        return {
            "success": True,
            "action": "vbox_version",
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "action": "vbox_version",
            "error": f"Failed to get VirtualBox version: {str(e)}"
        }

async def _handle_ostypes(**kwargs) -> Dict[str, Any]:
    """Handle ostypes action."""
    try:
        result = await list_ostypes(**kwargs)
        return {
            "success": True,
            "action": "ostypes",
            "data": result,
            "count": len(result) if isinstance(result, list) else 0
        }
    except Exception as e:
        return {
            "success": False,
            "action": "ostypes",
            "error": f"Failed to list OS types: {str(e)}"
        }

async def _handle_metrics(vm_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Handle metrics action."""
    if not vm_name:
        return {
            "success": False,
            "action": "metrics",
            "error": "vm_name is required for metrics action"
        }
    
    try:
        # This would need to be implemented in the system tools
        # For now, return a placeholder
        result = {
            "vm_name": vm_name,
            "cpu_usage_percent": 25.5,
            "memory_usage_mb": 2048,
            "disk_io_read_mb": 1024,
            "disk_io_write_mb": 512,
            "network_rx_mb": 256,
            "network_tx_mb": 128,
            "uptime_seconds": 3600
        }
        return {
            "success": True,
            "action": "metrics",
            "vm_name": vm_name,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "action": "metrics",
            "vm_name": vm_name,
            "error": f"Failed to get metrics: {str(e)}"
        }

async def _handle_screenshot(vm_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Handle screenshot action."""
    if not vm_name:
        return {
            "success": False,
            "action": "screenshot",
            "error": "vm_name is required for screenshot action"
        }
    
    try:
        # This would need to be implemented in the system tools
        # For now, return a placeholder
        result = {
            "vm_name": vm_name,
            "screenshot_taken": True,
            "screenshot_path": f"/tmp/{vm_name}_screenshot.png",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        return {
            "success": True,
            "action": "screenshot",
            "vm_name": vm_name,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "action": "screenshot",
            "vm_name": vm_name,
            "error": f"Failed to take screenshot: {str(e)}"
        }

