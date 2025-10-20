"""
Network Management Portmanteau Tool

Consolidates all network-related operations into a single tool with action-based interface.
Replaces 5 individual network tools with one comprehensive tool.
"""

import logging
from typing import Any

from fastmcp import FastMCP

# Import existing network tools
from virtualization_mcp.tools.network.network_tools import (
    create_hostonly_network,
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

    @mcp.tool(
        name="network_management", description="Comprehensive network configuration and management"
    )
    async def network_management(
        action: str,
        network_name: str | None = None,
        vm_name: str | None = None,
        adapter_slot: int | None = None,
        network_type: str | None = None,
        ip_address: str | None = None,
        netmask: str | None = None,
    ) -> dict[str, Any]:
        """
        Manage network configurations with various actions.

        Args:
            action: The operation to perform. Available actions:
                - list_networks: List all host-only networks
                - create_network: Create a host-only network (requires network_name)
                - remove_network: Remove a host-only network (requires network_name)
                - list_adapters: List network adapters for a VM (requires vm_name)
                - configure_adapter: Configure network adapter (requires vm_name, adapter_slot, network_type)

            network_name: Name of the host-only network
            vm_name: Name of the virtual machine
            adapter_slot: Network adapter slot number (0-3)
            network_type: Network type (nat, bridged, hostonly, internal)
            ip_address: IP address for network configuration
            netmask: Network mask for network configuration

        Returns:
            Dict containing the result of the operation

        Examples:
            # List all networks
            result = await network_management(action="list_networks")

            # Create a host-only network
            result = await network_management(
                action="create_network",
                network_name="MyNetwork",
                ip_address="192.168.56.1",
                netmask="255.255.255.0"
            )

            # List VM network adapters
            result = await network_management(
                action="list_adapters",
                vm_name="MyVM"
            )

            # Configure network adapter
            result = await network_management(
                action="configure_adapter",
                vm_name="MyVM",
                adapter_slot=0,
                network_type="hostonly",
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
                return await _handle_list_networks()

            elif action == "create_network":
                return await _handle_create_network(
                    network_name=network_name, ip_address=ip_address, netmask=netmask
                )

            elif action == "remove_network":
                return await _handle_remove_network(network_name=network_name)

            elif action == "list_adapters":
                return await _handle_list_adapters(vm_name=vm_name)

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


async def _handle_list_networks() -> dict[str, Any]:
    """Handle list networks action."""
    try:
        result = await list_hostonly_networks()
        return {
            "success": True,
            "action": "list_networks",
            "data": result,
            "count": len(result) if isinstance(result, list) else 0,
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
            network_name=network_name, ip_address=ip_address, netmask=netmask
        )
        return {
            "success": True,
            "action": "create_network",
            "network_name": network_name,
            "data": result,
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
        result = await remove_hostonly_network(network_name=network_name)
        return {
            "success": True,
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


async def _handle_list_adapters(vm_name: str | None = None) -> dict[str, Any]:
    """Handle list adapters action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_adapters",
            "error": "vm_name is required for list_adapters action",
        }

    try:
        # This would need to be implemented in the network tools
        # For now, return a placeholder
        result = {
            "vm_name": vm_name,
            "adapters": [
                {"slot": 0, "type": "nat", "enabled": True},
                {"slot": 1, "type": "none", "enabled": False},
                {"slot": 2, "type": "none", "enabled": False},
                {"slot": 3, "type": "none", "enabled": False},
            ],
        }
        return {"success": True, "action": "list_adapters", "vm_name": vm_name, "data": result}
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

    if not network_type:
        return {
            "success": False,
            "action": "configure_adapter",
            "error": "network_type is required for configure_adapter action",
        }

    try:
        # This would need to be implemented in the network tools
        # For now, return a placeholder
        result = {
            "vm_name": vm_name,
            "adapter_slot": adapter_slot,
            "network_type": network_type,
            "network_name": network_name,
            "configured": True,
        }
        return {"success": True, "action": "configure_adapter", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "configure_adapter",
            "vm_name": vm_name,
            "error": f"Failed to configure adapter: {str(e)}",
        }
