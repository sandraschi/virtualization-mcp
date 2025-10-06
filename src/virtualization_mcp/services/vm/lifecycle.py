"""
VM Lifecycle Management Module

This module provides core VM lifecycle operations including create, start, stop, and delete.
"""

import logging
from typing import Any, Dict, Optional

from ...vbox.manager import VBoxManagerError

logger = logging.getLogger(__name__)

class VMLifecycleMixin:
    """Mixin class providing VM lifecycle management methods."""
    
    def __init__(self, vm_service):
        """Initialize with a reference to the parent VMService."""
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations
    
    def create_vm(self, name: str, template: str = "ubuntu-dev", 
                 memory_mb: Optional[int] = None, 
                 disk_gb: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new VirtualBox virtual machine from a template with optional resource overrides.
        
        This function creates a new VM with the specified name using a predefined template.
        The template includes OS type, default resources, and initial configuration.
        
        Available templates:
        - ubuntu-dev: Ubuntu development environment (default)
        - minimal-linux: Lightweight Linux for quick tests
        - windows-test: Windows test environment
        - database-server: Pre-configured database server
        - web-server: Web server with common tools
        - docker-host: Docker-ready environment
        - security-test: Security testing environment
        - kubernetes-node: Kubernetes worker node
        - monitoring-stack: Monitoring tools pre-installed
        - jenkins-ci: Jenkins CI/CD server
        
        Args:
            name: Unique name for the new VM (must be unique across all VMs)
            template: Template name to use (e.g., "ubuntu-dev", "windows-test").
                Defaults to "ubuntu-dev".
            memory_mb: Memory allocation in MB (overrides template default).
                If not provided, uses template default.
            disk_gb: Disk size in GB (overrides template default).
                If not provided, uses template default.
                
        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_id": str,  # Internal VM identifier
                "name": str,   # VM name
                "ip_address": Optional[str],  # Assigned IP if available
                "warnings": List[str],  # Any non-critical warnings
                "message": str,  # Human-readable status message
                "next_steps": List[str],  # Suggested next actions
                "troubleshooting": List[str]  # Help for common issues
            }
        """
        warnings = []
        try:
            # Prepare custom settings if memory or disk is overridden
            custom_settings = {}
            if memory_mb is not None:
                custom_settings["memory_mb"] = memory_mb
            if disk_gb is not None:
                custom_settings["disk_gb"] = disk_gb
            
            # Create the VM using VMOperations
            result = self.vm_operations.create_vm(
                name=name,
                template=template,
                memory_mb=memory_mb,
                disk_gb=disk_gb,
                custom_settings=custom_settings
            )
            
            # Check if VM creation was successful
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error creating VM")
                raise VBoxManagerError(error_msg)
            
            # Prepare response
            vm_info = result.get("vm_info", {})
            response = {
                "status": "success",
                "vm_id": vm_info.get("uuid", ""),
                "name": name,
                "ip_address": vm_info.get("ip_address"),
                "warnings": warnings,
                "message": f"✓ VM '{name}' created successfully from template '{template}'",
                "next_steps": [
                    f"Start the VM: start_vm('{name}')",
                    f"Take initial snapshot: create_snapshot('{name}', 'initial')",
                    "Configure additional settings as needed"
                ],
                "troubleshooting": [
                    "If VM fails to start, check VirtualBox logs for errors",
                    "Ensure your system has enough resources (CPU, memory, disk)",
                    "Verify network settings if the VM can't connect to the network"
                ]
            }
            
            # Add any warnings from the operation
            if "warnings" in result:
                warnings.extend(result["warnings"])
                response["warnings"] = warnings
            
            return response
            
        except VBoxManagerError as e:
            logger.error(f"Failed to create VM '{name}': {e}", exc_info=True)
            return {
                "status": "error",
                "name": name,
                "error": str(e),
                "message": f"Failed to create VM '{name}': {e}",
                "troubleshooting": [
                    "Verify the VM name is unique and follows naming conventions",
                    "Check if the template exists and is accessible",
                    "Ensure you have sufficient disk space and memory available",
                    "Check VirtualBox logs for detailed error information"
                ]
            }
    
    def start_vm(self, name: str, headless: bool = True) -> Dict[str, Any]:
        """
        Start a VirtualBox virtual machine.
        
        This function starts the specified virtual machine in either headless (default) or
        GUI mode. Headless mode is recommended for automation as it doesn't require a display.
        
        The VM must be in a powered-off or saved state to be started. If the VM is already
        running, this function will return a success status with a message indicating that
        the VM was already running.
        
        Args:
            name: Name of the VM to start (must exist and be powered off or saved)
            headless: If True (default), starts the VM without a GUI.
                Set to False to show the VM window (requires a display server).
        
        Returns:
            Dict[str, Any]: {
                "status": "success"|"error"|"already_running",
                "vm_name": str,  # Name of the VM
                "state": str,    # New VM state ("running", "paused", "saved", etc.)
                "headless": bool,  # Whether started in headless mode
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }
        
        Example:
            >>> start_vm("my-ubuntu", headless=True)
            {
                "status": "success",
                "vm_name": "my-ubuntu",
                "state": "running",
                "headless": true,
                "message": "✓ VM 'my-ubuntu' started successfully in headless mode",
                "troubleshooting": [
                    "If VM fails to start, check the VirtualBox logs",
                    "Ensure the VM is not already running",
                    "Verify the VM exists and is in a startable state"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' does not exist")
            
            # Get current VM state
            vm_info = self.vbox_manager.get_vm_info(name)
            current_state = vm_info.get('VMState', '').lower()
            
            # Handle different VM states
            if current_state == 'running':
                return {
                    "status": "success",
                    "vm_name": name,
                    "state": "running",
                    "headless": headless,
                    "message": f"✓ VM '{name}' is already running",
                    "troubleshooting": [
                        "If you want to restart the VM, stop it first and then start it again"
                    ]
                }
            elif current_state not in ['poweroff', 'saved', 'aborted']:
                raise VBoxManagerError(
                    f"Cannot start VM '{name}' from state '{current_state}'. "
                    "VM must be powered off, saved, or aborted."
                )
            
            # Start the VM
            result = self.vm_operations.start_vm(name, headless=headless)
            
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error starting VM")
                raise VBoxManagerError(error_msg)
            
            # Get updated VM state
            vm_info = self.vbox_manager.get_vm_info(name)
            new_state = vm_info.get('VMState', 'unknown').lower()
            
            # Prepare response
            mode = "headless" if headless else "GUI"
            response = {
                "status": "success",
                "vm_name": name,
                "state": new_state,
                "headless": headless,
                "message": f"✓ VM '{name}' started successfully in {mode} mode",
                "troubleshooting": [
                    f"If the VM doesn't start, check VirtualBox logs: {self.vbox_manager.log_path}",
                    "Verify the VM's network settings if it starts but has no internet",
                    "Check the VM's storage settings if it fails to boot"
                ]
            }
            
            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]
            
            return response
            
        except VBoxManagerError as e:
            logger.error(f"Failed to start VM '{name}': {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": name,
                "state": current_state if 'current_state' in locals() else 'unknown',
                "headless": headless,
                "error": str(e),
                "message": f"Failed to start VM '{name}': {e}",
                "troubleshooting": [
                    f"Check if VM '{name}' exists and is accessible",
                    "Verify the VM is in a startable state (powered off, saved, or aborted)",
                    f"Check VirtualBox logs for more details: {getattr(self.vbox_manager, 'log_path', '')}",
                    "Ensure your system has enough resources (CPU, memory) to start the VM"
                ]
            }
    
    def stop_vm(self, name: str, force: bool = False) -> Dict[str, Any]:
        """
        Stop a running VirtualBox virtual machine gracefully or forcefully.
        
        This function stops the specified virtual machine using either a graceful shutdown
        (ACPI signal) or a forced power-off. A graceful shutdown is preferred as it allows
        the guest OS to shut down properly, but a forced stop may be necessary if the VM
        is unresponsive.
        
        Args:
            name: Name of the VM to stop (must be running or paused)
            force: If True, performs a hard power-off (equivalent to
                pulling the power cord). If False (default), attempts a graceful shutdown.
        
        Returns:
            Dict[str, Any]: {
                "status": "success"|"error"|"already_stopped",
                "vm_name": str,  # Name of the VM
                "force": bool,   # Whether forced stop was used
                "previous_state": str,  # State before stopping ("running", "paused", etc.)
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }
        
        Example:
            >>> stop_vm("my-ubuntu", force=False)
            {
                "status": "success",
                "vm_name": "my-ubuntu",
                "force": false,
                "previous_state": "running",
                "message": "✓ VM 'my-ubuntu' was gracefully shut down",
                "troubleshooting": [
                    "If graceful shutdown fails, try force=True",
                    "Check if the VM is responding to ACPI events",
                    "Verify the VM exists and is running"
                ]
            }
            
            >>> stop_vm("unresponsive-vm", force=True)
            {
                "status": "success",
                "vm_name": "unresponsive-vm",
                "force": true,
                "previous_state": "running",
                "message": "✓ VM 'unresponsive-vm' was forcefully powered off",
                "warning": "Forced power-off may cause data loss",
                "troubleshooting": [
                    "Check the VM logs for any file system errors on next boot",
                    "Consider using graceful shutdown when possible"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' does not exist")
            
            # Get current VM state
            vm_info = self.vbox_manager.get_vm_info(name)
            current_state = vm_info.get('VMState', '').lower()
            
            # Handle different VM states
            if current_state in ['poweroff', 'aborted', 'saved']:
                return {
                    "status": "success",
                    "vm_name": name,
                    "force": force,
                    "previous_state": current_state,
                    "message": f"VM '{name}' is already stopped (state: {current_state})",
                    "troubleshooting": [
                        "No action needed - the VM is already in a stopped state"
                    ]
                }
            
            if current_state not in ['running', 'paused']:
                raise VBoxManagerError(
                    f"Cannot stop VM '{name}' from state '{current_state}'. "
                    "VM must be running or paused."
                )
            
            # Stop the VM using VMOperations
            result = self.vm_operations.stop_vm(name=name, force=force)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error stopping VM')
                raise VBoxManagerError(error_msg)
            
            # Prepare response
            response = {
                "status": "success",
                "vm_name": name,
                "force": force,
                "previous_state": current_state,
                "message": (
                    f"✓ VM '{name}' was {'forcefully powered off' if force else 'gracefully shut down'}"
                ),
                "troubleshooting": [
                    f"VM was previously in state: {current_state}",
                    "Use 'list_vms()' to verify the current state"
                ]
            }
            
            # Add warning if force was used
            if force:
                response["warning"] = "Forced power-off may cause data loss"
                response["troubleshooting"].extend([
                    "Check the VM's file system for errors on next boot",
                    "Consider using graceful shutdown (force=False) when possible"
                ])
            
            # Add any warnings from the operation
            if "warnings" in result:
                if "warnings" not in response:
                    response["warnings"] = []
                response["warnings"].extend(result["warnings"])
            
            return response
            
        except VBoxManagerError as e:
            logger.error(f"Failed to stop VM '{name}': {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": name,
                "force": force,
                "previous_state": current_state if 'current_state' in locals() else 'unknown',
                "error": str(e),
                "message": f"Failed to stop VM '{name}': {e}",
                "troubleshooting": [
                    f"Current VM state: {current_state if 'current_state' in locals() else 'unknown'}",
                    "Try using force=True if the VM is unresponsive",
                    f"Check VirtualBox logs for more details: {getattr(self.vbox_manager, 'log_path', '')}",
                    "Ensure you have sufficient permissions to control the VM"
                ]
            }
    
    def delete_vm(self, name: str, delete_disks: bool = True) -> Dict[str, Any]:
        """
        Delete a VirtualBox virtual machine and optionally its associated disk files.
        
        This function permanently removes a virtual machine from VirtualBox. By default, it also
        deletes all associated disk files to prevent disk space leaks. Set delete_disks=False
        to keep the disk files (useful if they are shared with other VMs).
        
        WARNING: This action cannot be undone. All snapshots and saved states will be lost.
        
        Args:
            name: Name of the VM to delete (must be powered off or saved)
            delete_disks: If True (default), deletes all associated disk files.
                Set to False to keep the disk files in their current location.
        
        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the deleted VM
                "disks_deleted": bool,  # Whether disk files were deleted
                "disks_kept": List[str],  # List of disk files that were kept (if delete_disks=False)
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }
        
        Example:
            >>> delete_vm("old-vm", delete_disks=True)
            {
                "status": "success",
                "vm_name": "old-vm",
                "disks_deleted": true,
                "message": "✓ VM 'old-vm' and all associated disk files have been deleted",
                "troubleshooting": [
                    "This action cannot be undone",
                    "Check that all VM files have been removed from the filesystem"
                ]
            }
            
            >>> delete_vm("shared-disk-vm", delete_disks=False)
            {
                "status": "success",
                "vm_name": "shared-disk-vm",
                "disks_deleted": false,
                "disks_kept": [
                    "/path/to/disk.vdi"
                ],
                "message": "✓ VM 'shared-disk-vm' has been deleted (disk files were kept)",
                "troubleshooting": [
                    "The following disk files were not deleted: /path/to/disk.vdi",
                    "Manually delete these files if they are no longer needed"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' does not exist")
            
            # Get VM info before deletion to handle disk files
            vm_info = self.vbox_manager.get_vm_info(name)
            current_state = vm_info.get('VMState', '').lower()
            
            # Check if VM is running
            if current_state == 'running':
                raise VBoxManagerError(
                    f"Cannot delete running VM '{name}'. Stop the VM first."
                )
            
            # Get list of disk files before deletion
            disk_files = []
            if not delete_disks:
                # Get list of disk files to report which ones were kept
                disk_files = vm_info.get('storage', {}).get('disks', [])
            
            # Delete the VM using VMOperations
            result = self.vm_operations.delete_vm(name=name, delete_disks=delete_disks)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error deleting VM')
                raise VBoxManagerError(error_msg)
            
            # Prepare response
            response = {
                "status": "success",
                "vm_name": name,
                "disks_deleted": delete_disks,
                "message": (
                    f"✓ VM '{name}' and all associated disk files have been deleted" 
                    if delete_disks 
                    else f"✓ VM '{name}' has been deleted (disk files were kept)"
                ),
                "troubleshooting": [
                    "This action cannot be undone",
                    "Verify the VM no longer appears in VirtualBox Manager"
                ]
            }
            
            # Add disk information if disks were kept
            if not delete_disks and disk_files:
                response["disks_kept"] = disk_files
                response["troubleshooting"].append(
                    f"{len(disk_files)} disk files were not deleted"
                )
            
            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]
            
            return response
            
        except VBoxManagerError as e:
            logger.error(f"Failed to delete VM '{name}': {e}", exc_info=True)
            
            # Special handling for common error cases
            troubleshooting = [
                f"Check if VM '{name}' exists and is powered off",
                "Verify you have sufficient permissions to delete VM files"
            ]
            
            if 'running' in str(e).lower():
                troubleshooting.append("Stop the VM before attempting to delete it")
            
            return {
                "status": "error",
                "vm_name": name,
                "disks_deleted": False,
                "error": str(e),
                "message": f"Failed to delete VM '{name}': {e}",
                "troubleshooting": troubleshooting
            }
    
    def list_vms(self, details: bool = False, state_filter: str = "all") -> Dict[str, Any]:
        """
        List all VirtualBox virtual machines with their current states.
        
        This function returns a list of all VMs registered in VirtualBox, along with
        their current state (running, powered off, saved, etc.). When details=True,
        additional information about each VM is included, such as memory, CPU count,
        and storage details.
        
        Args:
            details: If True, includes detailed information about each VM.
                If False (default), only basic information is returned.
            state_filter: Filter VMs by state ("all", "running", "poweroff", "saved", etc.)
                Defaults to "all" which returns all VMs regardless of state.
        
        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "count": int,  # Number of VMs found
                "filtered_count": int,  # Number of VMs after applying state filter
                "vms": List[Dict[str, Any]],  # List of VM information dictionaries
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }
            
            Each VM in the "vms" list contains at least:
            {
                "name": str,      # VM name
                "state": str,     # Current state ("running", "poweroff", etc.)
                "uuid": str,      # Unique VM identifier
                "os_type": str,   # Guest OS type
                "memory_mb": int, # Allocated memory in MB
                "cpus": int,     # Number of virtual CPUs
                "storage_gb": float  # Total disk space in GB (if details=True)
            }
        
        Example:
            >>> list_vms()
            {
                "status": "success",
                "count": 2,
                "filtered_count": 2,
                "vms": [
                    {
                        "name": "ubuntu-vm",
                        "state": "running",
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "os_type": "Ubuntu_64",
                        "memory_mb": 2048,
                        "cpus": 2,
                        "storage_gb": 30.0
                    },
                    {
                        "name": "windows-vm",
                        "state": "poweroff",
                        "uuid": "123e4567-e89b-12d3-a456-426614174001",
                        "os_type": "Windows10_64",
                        "memory_mb": 4096,
                        "cpus": 4,
                        "storage_gb": 60.5
                    }
                ],
                "message": "Found 2 virtual machines",
                "troubleshooting": [
                    "Use list_vms(details=True) for more information about each VM",
                    "If a VM is missing, verify it's registered in VirtualBox"
                ]
            }
        """
        try:
            # Get list of all VMs using VMOperations
            result = self.vm_operations.list_vms(details=details)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error listing VMs')
                raise VBoxManagerError(error_msg)
            
            # Get the list of VMs
            vms = result.get('vms', [])
            
            # Apply state filter if specified
            filtered_vms = vms
            if state_filter.lower() != 'all':
                filtered_vms = [
                    vm for vm in vms 
                    if vm.get('state', '').lower() == state_filter.lower()
                ]
            
            # Prepare response
            response = {
                "status": "success",
                "count": len(vms),
                "filtered_count": len(filtered_vms),
                "vms": filtered_vms,
                "message": f"Found {len(vms)} virtual machine{'s' if len(vms) != 1 else ''}" +
                          (f" (filtered: {len(filtered_vms)})" if state_filter != 'all' else ''),
                "troubleshooting": [
                    "Use list_vms(details=True) for more information about each VM",
                    "If a VM is missing, verify it's registered in VirtualBox"
                ]
            }
            
            # Add a note if no VMs were found
            if not vms:
                response["message"] = "No virtual machines found"
                response["troubleshooting"] = [
                    "Use create_vm() to create a new virtual machine",
                    "Check if VirtualBox is properly installed and running"
                ]
            # Add a note if filter returned no results
            elif not filtered_vms and state_filter != 'all':
                response["message"] = f"No VMs found with state '{state_filter}'"
                response["troubleshooting"] = [
                    f"Available states: {', '.join(set(vm.get('state', 'unknown') for vm in vms))}",
                    "Use list_vms(details=True) to see all VMs"
                ]
            
            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]
            
            return response
            
        except VBoxManagerError as e:
            logger.error(f"Failed to list VMs: {e}", exc_info=True)
            
            # Special handling for common error cases
            troubleshooting = [
                "Check if VirtualBox is properly installed and running",
                "Verify you have sufficient permissions to access VirtualBox"
            ]
            
            if 'not found' in str(e).lower() or 'not installed' in str(e).lower():
                troubleshooting.append("Ensure VirtualBox is properly installed")
            
            return {
                "status": "error",
                "count": 0,
                "filtered_count": 0,
                "vms": [],
                "error": str(e),
                "message": f"Failed to list VMs: {e}",
                "troubleshooting": troubleshooting
            }



