"""
VM Storage Management Module

This module provides functionality for managing VM storage including disks and ISOs.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def storage_operation(func):
    """Decorator for storage operations with error handling and logging."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Storage operation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation": func.__name__,
                "vm_name": kwargs.get('vm_name', 'unknown')
            }
    return wrapper

class VMStorageMixin:
    """Mixin class providing VM storage management methods."""
    
    def __init__(self, vm_service):
        """Initialize with a reference to the parent VMService."""
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations
    
    @storage_operation
    def attach_disk(self, vm_name: str, disk_path: str, port: int = 0, 
                   device: int = 0, disk_type: str = "hdd") -> Dict[str, Any]:
        """
        Attach a virtual disk to a virtual machine.
        
        This method attaches a virtual disk (VDI, VMDK, VHD, etc.) to the specified
        VM at the given controller port and device number.
        
        API Endpoint: POST /vms/{vm_name}/storage/attach
        
        Args:
            vm_name: Name of the VM to attach the disk to
            disk_path: Absolute path to the virtual disk file
            port: Controller port number (0-3, default: 0)
            device: Device number on the port (0-1, default: 0)
            disk_type: Type of disk ("hdd" or "dvd", default: "hdd")
            
        Returns:
            Dictionary containing the result of the operation and disk details
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the VM is not found or if there's an error
                         attaching the disk
                         
        Example:
            ```python
            # Attach a virtual hard disk
            result = storage.attach_disk(
                vm_name="my-vm",
                disk_path="/path/to/disk.vdi",
                port=0,
                device=0,
                disk_type="hdd"
            )
            
            # Attach a DVD ISO
            result = storage.attach_disk(
                vm_name="my-vm",
                disk_path="/path/to/os.iso",
                disk_type="dvd"
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not disk_path or not os.path.isfile(disk_path):
            raise ValueError(f"Disk file not found: {disk_path}")
        if not 0 <= port <= 3:
            raise ValueError("Port must be between 0 and 3")
        if not 0 <= device <= 1:
            raise ValueError("Device must be 0 or 1")
        if disk_type.lower() not in ("hdd", "dvd"):
            raise ValueError("disk_type must be 'hdd' or 'dvd'")
        
        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")
        
        # Open a session
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for configuration
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)
            
            # Get the storage controller
            storage_ctl = session.machine.get_storage_controller_by_name("SATA Controller")
            if not storage_ctl:
                # Create a SATA controller if it doesn't exist
                storage_ctl = session.machine.add_storage_controller(
                    "SATA Controller",
                    self.vbox_manager.constants.StorageBus_SATA
                )
            
            # Attach the disk
            medium = self.vbox_manager.vbox.open_medium(
                disk_path,
                self.vbox_manager.constants.DeviceType_HardDisk if disk_type == "hdd" else self.vbox_manager.constants.DeviceType_DVD,
                self.vbox_manager.constants.AccessMode_ReadWrite,
                False
            )
            
            session.machine.attach_device(
                "SATA Controller",
                port,
                device,
                self.vbox_manager.constants.DeviceType_HardDisk if disk_type == "hdd" else self.vbox_manager.constants.DeviceType_DVD,
                medium
            )
            
            # Save settings
            session.machine.save_settings()
            
            return {
                "status": "success",
                "message": f"Disk attached to VM '{vm_name}' at port {port}, device {device}",
                "vm_name": vm_name,
                "disk_path": disk_path,
                "port": port,
                "device": device,
                "disk_type": disk_type
            }
            
        finally:
            session.unlock_machine()
    
    @storage_operation
    def detach_disk(self, vm_name: str, port: int, device: int) -> Dict[str, Any]:
        """
        Detach a virtual disk from a virtual machine.
        
        This method detaches a virtual disk from the specified VM at the given
        controller port and device number.
        
        API Endpoint: POST /vms/{vm_name}/storage/detach
        
        Args:
            vm_name: Name of the VM to detach the disk from
            port: Controller port number (0-3)
            device: Device number on the port (0-1)
            
        Returns:
            Dictionary containing the result of the operation
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the VM is not found or if there's an error
                         detaching the disk
                         
        Example:
            ```python
            # Detach a disk from port 0, device 0
            result = storage.detach_disk(
                vm_name="my-vm",
                port=0,
                device=0
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not 0 <= port <= 3:
            raise ValueError("Port must be between 0 and 3")
        if not 0 <= device <= 1:
            raise ValueError("Device must be 0 or 1")
        
        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")
        
        # Open a session
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for configuration
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)
            
            # Detach the disk
            session.machine.detach_device("SATA Controller", port, device)
            
            # Save settings
            session.machine.save_settings()
            
            return {
                "status": "success",
                "message": f"Disk detached from VM '{vm_name}' at port {port}, device {device}",
                "vm_name": vm_name,
                "port": port,
                "device": device
            }
            
        finally:
            session.unlock_machine()
            return {"status": "error", "error": str(e)}
    
    def create_disk(self, disk_path: str, size_gb: int, 
                   format_type: str = "vdi") -> Dict[str, Any]:
        """
        Create a new virtual disk.
        
        Args:
            disk_path: Path where to create the disk
            size_gb: Size of the disk in GB
            format_type: Disk format (vdi, vmdk, vhd, etc.)
            
        Returns:
            Dict containing status and disk creation details
        """
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to create disk at {disk_path}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def resize_disk(self, disk_path: str, new_size_gb: int) -> Dict[str, Any]:
        """
        Resize an existing virtual disk.
        
        Args:
            disk_path: Path to the disk file
            new_size_gb: New size in GB
            
        Returns:
            Dict containing status and resize operation result
        """
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to resize disk {disk_path}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}



