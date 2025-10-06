"""
Port forwarding management for VirtualBox VMs.

This module handles all operations related to port forwarding rules
for NAT and NAT Network adapters.
"""

import logging
from typing import Dict, List, Optional

from ....vbox.manager import VBoxManagerError
from .types import PortForwardingRule, NetworkOperationResult

logger = logging.getLogger(__name__)


class PortForwardingService:
    """Service for managing VM port forwarding rules."""

    def __init__(self, vbox_manager):
        """Initialize with a VBoxManager instance."""
        self.vbox_manager = vbox_manager

    def add_port_forwarding_rule(
        self,
        vm_name: str,
        adapter_number: int,
        rule: PortForwardingRule
    ) -> NetworkOperationResult:
        """
        Add a port forwarding rule to a NAT adapter.
        
        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            rule: Port forwarding rule to add
            
        Returns:
            NetworkOperationResult with the operation status
        """
        try:
            if not 1 <= adapter_number <= 4:
                raise ValueError("Adapter number must be between 1 and 4")
                
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Build VBoxManage command
            cmd = [
                "modifyvm", vm_name,
                f"--natpf{adapter_number}",
                f"{rule.name},{rule.protocol},,{rule.host_port},,{rule.guest_port}"
            ]
            
            if rule.host_ip:
                cmd[-1] = cmd[-1].replace(",,", f",{rule.host_ip},", 1)
            if rule.guest_ip:
                # Replace the last occurrence of ,, with ,guest_ip,
                parts = cmd[-1].rsplit(",,", 1)
                cmd[-1] = f"{parts[0]},{rule.guest_ip},{parts[1]}"
            
            # Execute the command
            self.vbox_manager.run_command(cmd)
            
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "message": f"Port forwarding rule '{rule.name}' added successfully",
                "troubleshooting": []
            }
            
        except (ValueError, VBoxManagerError) as e:
            logger.error(
                f"Failed to add port forwarding rule '{rule.name}' to adapter {adapter_number} "
                f"for VM {vm_name}: {e}"
            )
            return {
                "status": "error",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "error": str(e),
                "message": f"Failed to add port forwarding rule: {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check that the adapter number is valid (1-4)",
                    "Ensure the ports are not already in use"
                ]
            }

    def remove_port_forwarding_rule(
        self,
        vm_name: str,
        adapter_number: int,
        rule_name: str
    ) -> NetworkOperationResult:
        """
        Remove a port forwarding rule from a NAT adapter.
        
        Args:
            vm_name: Name of the VM
            adapter_number: Adapter number (1-4)
            rule_name: Name of the rule to remove
            
        Returns:
            NetworkOperationResult with the operation status
        """
        try:
            if not 1 <= adapter_number <= 4:
                raise ValueError("Adapter number must be between 1 and 4")
                
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Build VBoxManage command to remove the rule
            cmd = [
                "modifyvm", vm_name,
                f"--natpf{adapter_number}",
                f"delete",
                rule_name
            ]
            
            # Execute the command
            self.vbox_manager.run_command(cmd)
            
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "message": f"Port forwarding rule '{rule_name}' removed successfully",
                "troubleshooting": []
            }
            
        except (ValueError, VBoxManagerError) as e:
            logger.error(
                f"Failed to remove port forwarding rule '{rule_name}' from adapter {adapter_number} "
                f"for VM {vm_name}: {e}"
            )
            return {
                "status": "error",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "error": str(e),
                "message": f"Failed to remove port forwarding rule: {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check that the adapter number is valid (1-4)",
                    "Ensure the rule name is correct"
                ]
            }



