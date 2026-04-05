"""
Network Management Portmanteau Tool

Consolidates all network-related operations into a single tool with action-based interface.
Replaces 5 individual network tools with one comprehensive tool.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

# Import existing network tools
from virtualization_mcp.tools.network.network_tools import (
    configure_network_adapter,
    create_hostonly_network,
    list_network_adapters,
    list_hostonly_networks,
    remove_hostonly_network,
)

logger = logging.getLogger(__name__)

# Define available actions
NETWORK_ACTIONS = {
    "list_networks": "List all host-only networks",
    "create_network": "Create a host-only network",
    "remove_network": "Remove a host-only network",
    "list_adapters": "List network adapters for a VM",
    "configure_adapter": "Configure network adapter for a VM",
}


def register_network_management_tool(mcp: FastMCP) -> None:
    """Register the network management portmanteau tool."""

    @mcp.tool()
    async def network_management(
        action: Literal["list_networks", "create_network", "remove_network", "list_adapters", "configure_adapter"],
        network_name: str | None = None,
        vm_name: str | None = None,
        adapter_slot: int | None = None,
        network_type: str | None = None,
        ip_address: str | None = None,
        netmask: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Comprehensive network management portmanteau tool.
        
        This tool consolidates all network operations into a single interface. Use the 'action' parameter
        to specify which operation to perform. Different actions require different parameters.

        Args:
            action (required): The operation to perform. Must be one of:
                - "list_networks": List all host-only networks (no other parameters required)
                - "create_network": Create a host-only network (requires: network_name)
                - "remove_network": Remove a host-only network (requires: network_name)
                - "list_adapters": List network adapters for a VM (requires: vm_name)
                - "configure_adapter": Configure network adapter for a VM (requires: vm_name, adapter_slot, network_type)

            network_name: Name of the host-only network (required for create_network, remove_network, configure_adapter)
            vm_name: Name of the virtual machine (required for list_adapters, configure_adapter)
            adapter_slot: Network adapter slot number 0-3 (required for configure_adapter)
            network_type: Network type for adapter configuration (required for configure_adapter).
                          Valid values: "nat", "bridged", "hostonly", "internal", "generic", "natnetwork"
            ip_address: IP address for network configuration (optional for create_network)
            netmask: Network mask for network configuration (optional for create_network)

        Returns:
            Dict containing:
                - success: Boolean indicating if operation succeeded
                - action: The action that was performed
                - data: Operation-specific result data
                - error: Error message if success is False
                - count: Number of networks/adapters (for list actions)

        Examples:
            # List all host-only networks - simplest usage, no other parameters needed
            result = await network_management(action="list_networks")

            # Create a host-only network - requires network_name
            result = await network_management(
                action="create_network",
                network_name="MyNetwork",
                ip_address="192.168.56.1",
                netmask="255.255.255.0"
            )

            # List VM network adapters - requires vm_name
            result = await network_management(
                action="list_adapters",
                vm_name="MyVM"
            )

            # Configure network adapter - requires vm_name, adapter_slot, network_type
            result = await network_management(
                action="configure_adapter",
                vm_name="MyVM",
                adapter_slot=0,
                network_type="hostonly",
                network_name="MyNetwork"
            )

            # Remove a network - requires network_name
            result = await network_management(
                action="remove_network",
                network_name="MyNetwork"
            )
        """
        try:
            # Validate action
            if action not in NETWORK_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(NETWORK_ACTIONS.keys())}",
                    "available_actions": NETWORK_ACTIONS,
                }

            logger.info(f"Executing network management action: {action}")

            # Route to appropriate function based on action
            if action == "list_networks":
                return await _handle_list_networks(limit=limit, offset=offset)

            elif action == "create_network":
                return await _handle_create_network(
                    network_name=network_name, ip_address=ip_address, netmask=netmask
                )

            elif action == "remove_network":
                return await _handle_remove_network(network_name=network_name)

            elif action == "list_adapters":
                return await _handle_list_adapters(vm_name=vm_name, limit=limit, offset=offset)

            elif action == "configure_adapter":
                return await _handle_configure_adapter(
                    vm_name=vm_name,
                    adapter_slot=adapter_slot,
                    network_type=network_type,
                    network_name=network_name,
                )

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": NETWORK_ACTIONS,
                }

        except Exception as e:
            logger.error(f"Error in network management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "available_actions": NETWORK_ACTIONS,
            }


def _paginate(items: list[dict[str, Any]], limit: int, offset: int) -> dict[str, Any]:
    lim = max(1, min(int(limit), 500))
    off = max(0, int(offset))
    page = items[off : off + lim]
    return {
        "items": page,
        "count": len(page),
        "total": len(items),
        "limit": lim,
        "offset": off,
        "has_more": off + len(page) < len(items),
    }


async def _handle_list_networks(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Handle list networks action."""
    try:
        result = await list_hostonly_networks()
        ok = isinstance(result, dict) and result.get("status") == "success"
        all_networks = result.get("networks", []) if isinstance(result, dict) else []
        page = _paginate(all_networks if isinstance(all_networks, list) else [], limit, offset)
        return {
            "success": ok,
            "action": "list_networks",
            "data": result,
            "count": page["count"],
            "total": page["total"],
            "limit": page["limit"],
            "offset": page["offset"],
            "has_more": page["has_more"],
            "items": page["items"],
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list_networks",
            "error": f"Failed to list networks: {str(e)}",
        }


async def _handle_create_network(
    network_name: str | None = None,
    ip_address: str | None = None,
    netmask: str | None = None,
) -> dict[str, Any]:
    """Handle create network action."""
    if not network_name:
        return {
            "success": False,
            "action": "create_network",
            "error": "network_name is required for create_network action",
        }

    try:
        result = await create_hostonly_network(
            network_name=network_name, ip=ip_address or "", netmask=netmask or "255.255.255.0"
        )
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "create_network",
            "network_name": network_name,
            "data": result,
            "recovery_options": None
            if isinstance(result, dict) and result.get("status") == "success"
            else [
                "Provide ip_address (e.g. 192.168.56.1) and valid netmask",
                "Ensure VBoxManage can create host-only adapters on this host",
            ],
        }
    except Exception as e:
        return {
            "success": False,
            "action": "create_network",
            "network_name": network_name,
            "error": f"Failed to create network: {str(e)}",
        }


async def _handle_remove_network(network_name: str | None = None) -> dict[str, Any]:
    """Handle remove network action."""
    if not network_name:
        return {
            "success": False,
            "action": "remove_network",
            "error": "network_name is required for remove_network action",
        }

    try:
        result = await remove_hostonly_network(interface=network_name)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "remove_network",
            "network_name": network_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "remove_network",
            "network_name": network_name,
            "error": f"Failed to remove network: {str(e)}",
        }


async def _handle_list_adapters(
    vm_name: str | None = None, limit: int = 100, offset: int = 0
) -> dict[str, Any]:
    """Handle list adapters action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_adapters",
            "error": "vm_name is required for list_adapters action",
        }

    try:
        result = await list_network_adapters(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        adapters = result.get("adapters", [])
        page = _paginate(adapters if isinstance(adapters, list) else [], limit, offset)
        return {
            "success": ok,
            "action": "list_adapters",
            "vm_name": vm_name,
            "data": result,
            "count": page["count"],
            "total": page["total"],
            "limit": page["limit"],
            "offset": page["offset"],
            "has_more": page["has_more"],
            "items": page["items"],
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list_adapters",
            "vm_name": vm_name,
            "error": f"Failed to list adapters: {str(e)}",
        }


async def _handle_configure_adapter(
    vm_name: str | None = None,
    adapter_slot: int | None = None,
    network_type: str | None = None,
    network_name: str | None = None,
) -> dict[str, Any]:
    """Handle configure adapter action."""
    if not vm_name:
        return {
            "success": False,
            "action": "configure_adapter",
            "error": "vm_name is required for configure_adapter action",
        }

    if adapter_slot is None:
        return {
            "success": False,
            "action": "configure_adapter",
            "error": "adapter_slot is required for configure_adapter action",
        }
    if adapter_slot < 0 or adapter_slot > 3:
        return {
            "success": False,
            "action": "configure_adapter",
            "error": "adapter_slot must be in range 0..3",
        }

    if not network_type:
        return {
            "success": False,
            "action": "configure_adapter",
            "error": "network_type is required for configure_adapter action",
        }

    try:
        # network_tools uses adapter_id in range 1..4, while this tool accepts slot 0..3.
        adapter_id = adapter_slot + 1
        result = await configure_network_adapter(
            vm_name=vm_name, adapter_id=adapter_id, network_type=network_type
        )
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "configure_adapter",
            "vm_name": vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "configure_adapter",
            "vm_name": vm_name,
            "error": f"Failed to configure adapter: {str(e)}",
        }
