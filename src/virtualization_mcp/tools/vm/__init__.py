"""
VM Management Tools

This module contains tools for managing virtual machines across different hypervisors.
"""

# Import base VM tools
# Import Hyper-V tools (individual tools disabled - using portmanteau)
from .hyperv_tools import (
    VirtualMachine,
    VMDisk,
    VMNetworkAdapter,
    VMSize,
    VMSnapshot,
    VMState,
    # get_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
    # list_hyperv_vms,  # Disabled - use hyperv_management portmanteau tool
    # start_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
    # stop_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
)
from .vm_tools import *  # noqa: F403

__all__ = [  # noqa: F405
    "VMDisk",
    "VMNetworkAdapter",
    "VMSize",
    "VMSnapshot",
    # Hyper-V tools (individual tools disabled - using portmanteau)
    "VMState",
    "VirtualMachine",
    "clone_vm",
    "create_vm",
    "delete_vm",
    "get_vm_info",
    # Base VM tools
    "list_vms",
    "modify_vm",
    "pause_vm",
    "reset_vm",
    "resume_vm",
    "start_vm",
    "stop_vm",
    # "list_hyperv_vms",  # Disabled - use hyperv_management portmanteau tool
    # "get_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "start_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "stop_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
]
