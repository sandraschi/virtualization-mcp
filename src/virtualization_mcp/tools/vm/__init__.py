"""
VM Management Tools

This module contains tools for managing virtual machines across different hypervisors.
"""

# Import base VM tools
# Import Hyper-V tools
from .hyperv_tools import (
    VirtualMachine,
    VMDisk,
    VMNetworkAdapter,
    VMSize,
    VMSnapshot,
    VMState,
    get_hyperv_vm,
    list_hyperv_vms,
    start_hyperv_vm,
    stop_hyperv_vm,
)
from .vm_tools import *

__all__ = [
    # Base VM tools
    "list_vms",
    "get_vm_info",
    "start_vm",
    "stop_vm",
    "create_vm",
    "delete_vm",
    "clone_vm",
    "modify_vm",
    "reset_vm",
    "pause_vm",
    "resume_vm",
    # Hyper-V tools
    "VMState",
    "VMSize",
    "VMDisk",
    "VMSnapshot",
    "VMNetworkAdapter",
    "VirtualMachine",
    "list_hyperv_vms",
    "get_hyperv_vm",
    "start_hyperv_vm",
    "stop_hyperv_vm",
]
