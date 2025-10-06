"""
Network adapter management for VirtualBox VMs.

This module handles all operations related to VM network adapters,
including configuration, enabling/disabling, and status monitoring.
"""

import logging
from typing import Dict, List, Optional, cast

from ....vbox.manager import VBoxManagerError
from .types import (
    NetworkAdapterConfig,
    NetworkAdapterState,
    NetworkAdapterType,
    NetworkOperationResult,
)

logger = logging.getLogger(__name__)


class NetworkAdapterService:
    """Service for managing VM network adapters."""

    def __init__(self, vbox_manager):
        """Initialize with a VBoxManager instance."""
        self.vbox_manager = vbox_manager

    def get_network_adapters(self, vm_name: str) -> NetworkOperationResult:
        """
        Retrieve all network adapters for a virtual machine.
        
        Args:
            vm_name: Name of the virtual machine
            
        Returns:
            NetworkOperationResult with adapter details
        """
        try:
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # This would be implemented using VBoxManage commands
            # For now, returning a placeholder
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapters": [],
                "message": "Network adapters retrieved successfully",
                "troubleshooting": []
            }
            
        except VBoxManagerError as e:
            logger.error(f"Failed to get network adapters for VM {vm_name}: {e}")
            return {
                "status": "error",
                "vm_name": vm_name,
                "error": str(e),
                "message": f"Failed to get network adapters: {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check VirtualBox logs for more details"
                ]
            }

    def configure_adapter(
        self,
        vm_name: str,
        adapter_number: int,
        config: NetworkAdapterConfig
    ) -> NetworkOperationResult:
        """
        Configure a network adapter with the given settings.
        
        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            config: Configuration for the adapter
            
        Returns:
            NetworkOperationResult with the operation status
        """
        try:
            if not 1 <= adapter_number <= 4:
                raise ValueError("Adapter number must be between 1 and 4")
                
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Build VBoxManage command
            cmd = ["modifyvm", vm_name]
            
            # Set basic adapter properties
            cmd.extend([f"--nic{adapter_number}", config.adapter_type.value])
            cmd.extend([f"--cableconnected{adapter_number}", 
                       "on" if config.cable_connected else "off"])
            
            # Set type-specific properties
            if config.mac_address:
                cmd.extend([f"--macaddress{adapter_number}", config.mac_address])
                
            if config.adapter_type == NetworkAdapterType.BRIDGED and config.network_name:
                cmd.extend([f"--bridgeadapter{adapter_number}", config.network_name])
            elif config.adapter_type == NetworkAdapterType.HOST_ONLY and config.hostonly_interface:
                cmd.extend([f"--hostonlyadapter{adapter_number}", config.hostonly_interface])
            elif config.adapter_type == NetworkAdapterType.INTERNAL and config.internal_network:
                cmd.extend([f"--intnet{adapter_number}", config.internal_network])
            elif config.adapter_type == NetworkAdapterType.NAT_NETWORK and config.network_name:
                cmd.extend([f"--natnet{adapter_number}", config.network_name])
            
            # Set promiscuous mode if specified
            if hasattr(config, 'promiscuous_mode'):
                cmd.extend([f"--nicpromisc{adapter_number}", config.promiscuous_mode])
            
            # Execute the command
            self.vbox_manager.run_command(cmd)
            
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "message": f"Network adapter {adapter_number} configured successfully",
                "troubleshooting": []
            }
            
        except (ValueError, VBoxManagerError) as e:
            logger.error(f"Failed to configure adapter {adapter_number} for VM {vm_name}: {e}")
            return {
                "status": "error",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "error": str(e),
                "message": f"Failed to configure network adapter: {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check that the adapter number is valid (1-4)",
                    "Verify network settings are correct"
                ]
            }
