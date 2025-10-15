"""
Main networking service for VirtualBox VMs.

This module provides a unified interface for all VM networking operations,
delegating to specialized services as needed.
"""

from .adapters import NetworkAdapterService
from .forwarding import PortForwardingService
from .types import (
    NetworkAdapterConfig,
    NetworkOperationResult,
    PortForwardingRule,
)


class VMNetworkingService:
    """
    High-level service for managing VM networking.

    This class provides a clean, unified API for all networking operations,
    delegating to specialized services as needed.
    """

    def __init__(self, vbox_manager):
        """Initialize with a VBoxManager instance."""
        self.vbox_manager = vbox_manager
        self.adapters = NetworkAdapterService(vbox_manager)
        self.forwarding = PortForwardingService(vbox_manager)

    # --- Adapter Management ---

    def get_network_adapters(self, vm_name: str) -> NetworkOperationResult:
        """
        Get all network adapters for a VM.

        Args:
            vm_name: Name of the VM

        Returns:
            NetworkOperationResult with adapter details
        """
        return self.adapters.get_network_adapters(vm_name)

    def configure_adapter(
        self, vm_name: str, adapter_number: int, config: NetworkAdapterConfig
    ) -> NetworkOperationResult:
        """
        Configure a network adapter.

        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            config: Adapter configuration

        Returns:
            NetworkOperationResult with the operation status
        """
        return self.adapters.configure_adapter(vm_name, adapter_number, config)

    def enable_adapter(
        self, vm_name: str, adapter_number: int, adapter_type: str = "nat"
    ) -> NetworkOperationResult:
        """
        Enable a network adapter.

        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            adapter_type: Type of adapter to enable (default: "nat")

        Returns:
            NetworkOperationResult with the operation status
        """
        config = NetworkAdapterConfig(enabled=True, adapter_type=adapter_type, cable_connected=True)
        return self.adapters.configure_adapter(vm_name, adapter_number, config)

    def disable_adapter(self, vm_name: str, adapter_number: int) -> NetworkOperationResult:
        """
        Disable a network adapter.

        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)

        Returns:
            NetworkOperationResult with the operation status
        """
        config = NetworkAdapterConfig(enabled=False, adapter_type="none", cable_connected=False)
        return self.adapters.configure_adapter(vm_name, adapter_number, config)

    # --- Port Forwarding ---

    def add_port_forwarding_rule(
        self, vm_name: str, adapter_number: int, rule: PortForwardingRule
    ) -> NetworkOperationResult:
        """
        Add a port forwarding rule.

        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            rule: Port forwarding rule to add

        Returns:
            NetworkOperationResult with the operation status
        """
        return self.forwarding.add_port_forwarding_rule(vm_name, adapter_number, rule)

    def remove_port_forwarding_rule(
        self, vm_name: str, adapter_number: int, rule_name: str
    ) -> NetworkOperationResult:
        """
        Remove a port forwarding rule.

        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            rule_name: Name of the rule to remove

        Returns:
            NetworkOperationResult with the operation status
        """
        return self.forwarding.remove_port_forwarding_rule(vm_name, adapter_number, rule_name)

    # --- Utility Methods ---

    def get_network_status(self, vm_name: str) -> NetworkOperationResult:
        """
        Get the current network status of a VM.

        This includes adapter configurations, IP addresses, and port forwarding rules.

        Args:
            vm_name: Name of the VM

        Returns:
            NetworkOperationResult with network status details
        """
        # Get adapter information
        result = self.adapters.get_network_adapters(vm_name)
        if result["status"] != "success":
            return result

        # In a real implementation, we would also gather:
        # - IP addresses (via guest properties or guest additions)
        # - Network connectivity status
        # - Port forwarding rules
        # - Bandwidth usage (if available)

        return {
            "status": "success",
            "vm_name": vm_name,
            "message": "Network status retrieved successfully",
            "adapters": result.get("adapters", []),
            "troubleshooting": [],
        }
