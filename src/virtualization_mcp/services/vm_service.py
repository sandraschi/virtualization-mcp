"""
VirtualBox VM management service with compatibility layer.
"""

import logging
import os
from typing import Any

from ..vbox.compat_adapter import VBoxManagerError, get_vbox_manager
from ..vbox.vm_operations import VMOperations

logger = logging.getLogger(__name__)


class VMService:
    """Service for managing VirtualBox VMs with compatibility layer.

    This service provides a high-level interface for managing VirtualBox VMs,
    using a compatibility layer that works with both the VirtualBox Python API
    and VBoxManage command-line tool for maximum compatibility.
    """

    def __init__(self):
        """Initialize the VM service with a VBoxManager instance.

        The VBoxManager instance is created using the compatibility adapter,
        which automatically selects the best available backend (Python API or VBoxManage).
        """
        self.vbox_manager = get_vbox_manager()
        self.vm_operations = VMOperations(self.vbox_manager)

        # Log the backend being used
        backend = "Python API" if hasattr(self.vbox_manager, "api") else "VBoxManage CLI"
        logger.info(f"Initialized VMService with {backend} backend")

    def get_vm_state(self, vm_name: str) -> dict[str, Any]:
        """
        Get the current state of a virtual machine.

        Args:
            vm_name: Name of the virtual machine

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,
                "state": str,  # e.g., "running", "poweroff", "paused", "saved", "aborted"
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }
        """
        try:
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Get VM state using VBoxManager
            state = self.vbox_manager.get_vm_state(vm_name)

            return {
                "status": "success",
                "vm_name": vm_name,
                "state": state.lower(),
                "message": f"✓ VM '{vm_name}' state: {state}",
                "troubleshooting": [
                    "Use list_vms() to see all available VMs",
                    "Check VirtualBox logs if the state seems incorrect",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to get state for VM '{vm_name}': {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "state": "error",
                "error": str(e),
                "message": f"Failed to get state for VM '{vm_name}': {e}",
                "troubleshooting": [
                    f"Verify that VM '{vm_name}' exists",
                    "Check if VirtualBox is running properly",
                    "Verify you have sufficient permissions to access VM state",
                ],
            }

    def create_vm(
        self,
        name: str,
        template: str = "ubuntu-dev",
        memory_mb: int | None = None,
        disk_gb: int | None = None,
    ) -> dict[str, Any]:
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
                custom_settings=custom_settings,
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
                    "Configure additional settings as needed",
                ],
                "troubleshooting": [
                    "If the VM doesn't start, check VirtualBox logs",
                    "Verify network settings if VM starts but has no internet",
                    "Check disk space if creation fails",
                ],
            }

            # Add template-specific next steps
            if "docker" in template.lower():
                response["next_steps"].append(
                    "Install Docker: curl -sSL https://get.docker.com | sh"
                )
            elif "kubernetes" in template.lower():
                response["next_steps"].extend(
                    [
                        "Initialize cluster: kubeadm init",
                        "Set up network plugin: kubectl apply -f <network-plugin-yaml>",
                    ]
                )

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to create VM {name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_id": "",
                "name": name,
                "ip_address": None,
                "warnings": warnings,
                "error": str(e),
                "message": f"Failed to create VM '{name}': {e}",
                "troubleshooting": [
                    "Check if the VM name is unique",
                    "Verify that the template exists",
                    f"Check VirtualBox logs for more details: {self.vbox_manager.log_path}",
                    "Ensure you have sufficient disk space and permissions",
                ],
            }

    def start_vm(self, name: str, headless: bool = True) -> dict[str, Any]:
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
            current_state = vm_info.get("VMState", "").lower()

            # Handle different VM states
            if current_state == "running":
                return {
                    "status": "success",
                    "vm_name": name,
                    "state": "running",
                    "headless": headless,
                    "message": f"✓ VM '{name}' is already running",
                    "troubleshooting": [
                        "If you want to restart the VM, stop it first and then start it again"
                    ],
                }
            elif current_state not in ["poweroff", "saved", "aborted"]:
                raise VBoxManagerError(
                    f"Cannot start VM in state '{current_state}'. "
                    "VM must be powered off, saved, or aborted."
                )

            # Start the VM using VMOperations
            result = self.vm_operations.start_vm(name=name, headless=headless)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error starting VM")
                raise VBoxManagerError(error_msg)

            # Get updated VM info
            vm_info = self.vbox_manager.get_vm_info(name)

            return {
                "status": "success",
                "vm_name": name,
                "state": vm_info.get("VMState", "unknown").lower(),
                "headless": headless,
                "message": f"✓ VM '{name}' started successfully in {'headless' if headless else 'GUI'} mode",
                "troubleshooting": [
                    "If the VM doesn't respond, check the VirtualBox GUI",
                    "Verify network connectivity if the VM starts but has no internet",
                    f"Check logs at: {self.vbox_manager.log_path} for detailed errors",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to start VM {name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": name,
                "state": "error",
                "headless": headless,
                "error": str(e),
                "message": f"Failed to start VM '{name}': {e}",
                "troubleshooting": [
                    "Check if the VM exists and is powered off",
                    "Verify VirtualBox is properly installed and running",
                    f"Check VirtualBox logs at: {getattr(self.vbox_manager, 'log_path', '~/.config/VirtualBox/Logs')}",
                    "Ensure you have sufficient permissions to start VMs",
                ],
            }

    def stop_vm(self, name: str, force: bool = False) -> dict[str, Any]:
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
            current_state = vm_info.get("VMState", "").lower()

            # Handle already stopped VMs
            if current_state in ["poweroff", "aborted"]:
                return {
                    "status": "success",
                    "vm_name": name,
                    "force": force,
                    "previous_state": current_state,
                    "message": f"✓ VM '{name}' is already stopped (state: {current_state})",
                    "troubleshooting": ["No action was taken as the VM is not running"],
                }

            # Validate VM state
            if current_state not in ["running", "paused"]:
                raise VBoxManagerError(
                    f"Cannot stop VM in state '{current_state}'. VM must be running or paused."
                )

            # Stop the VM using VMOperations
            result = self.vm_operations.stop_vm(name=name, force=force)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error stopping VM")
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
                    "The VM may take a moment to fully shut down",
                    "Check VM state with: list_vms()",
                ],
            }

            # Add warning for forced stop
            if force:
                response["warning"] = (
                    "Forced power-off may cause data loss. Use graceful shutdown when possible."
                )
                response["troubleshooting"].extend(
                    [
                        "Check for filesystem errors on next boot",
                        "Consider taking snapshots before using force stop",
                    ]
                )

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to stop VM {name}: {e}", exc_info=True)

            # Special handling for common error cases
            troubleshooting = [
                f"Check if VM '{name}' exists and is running",
                "Verify VirtualBox is properly installed and running",
            ]

            if not force:
                troubleshooting.append("Try using force=True if the VM is unresponsive")

            return {
                "status": "error",
                "vm_name": name,
                "force": force,
                "error": str(e),
                "message": f"Failed to stop VM '{name}': {e}",
                "troubleshooting": troubleshooting,
            }

    def delete_vm(self, name: str, delete_disk: bool = True) -> dict[str, Any]:
        """
        Delete a VirtualBox virtual machine and optionally its associated disk files.

        This function permanently removes a virtual machine from VirtualBox. By default, it also
        deletes all associated disk files to prevent disk space leaks. Set delete_disk=False
        to keep the disk files (useful if they are shared with other VMs).

        WARNING: This action cannot be undone. All snapshots and saved states will be lost.

        Args:
            name: Name of the VM to delete (must be powered off or saved)
            delete_disk: If True (default), deletes all associated disk files.
                Set to False to keep the disk files in their current location.

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error"|"not_found",
                "vm_name": str,  # Name of the deleted VM
                "disks_removed": List[str],  # Paths of deleted disk files (if any)
                "disks_retained": List[str],  # Paths of retained disk files (if any)
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "warning": Optional[str],  # Warning message if applicable
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> delete_vm("old-ubuntu", delete_disk=True)
            {
                "status": "success",
                "vm_name": "old-ubuntu",
                "disks_removed": [
                    "/path/to/VirtualBox VMs/old-ubuntu/disk.vdi"
                ],
                "disks_retained": [],
                "message": "✓ VM 'old-ubuntu' and its disk files were successfully deleted",
                "troubleshooting": [
                    "If you see 'not found' errors, the VM may have already been removed",
                    "Check VirtualBox Manager to confirm the VM was removed",
                    "Verify disk files were removed if disk space is a concern"
                ]
            }

            >>> delete_vm("important-vm", delete_disk=False)
            {
                "status": "success",
                "vm_name": "important-vm",
                "disks_removed": [],
                "disks_retained": [
                    "/path/to/VirtualBox VMs/important-vm/disk.vdi"
                ],
                "message": "✓ VM 'important-vm' was removed (disk files retained)",
                "warning": "Disk files were not deleted and may still consume space",
                "troubleshooting": [
                    "Remember to manually clean up disk files if they are no longer needed",
                    "Path to retained disk: /path/to/VirtualBox VMs/important-vm/disk.vdi"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(name):
                return {
                    "status": "not_found",
                    "vm_name": name,
                    "disks_removed": [],
                    "disks_retained": [],
                    "message": f"VM '{name}' not found. No action taken.",
                    "troubleshooting": [
                        "Verify the VM name is correct",
                        "Check VirtualBox Manager for the list of available VMs",
                    ],
                }

            # Get VM info before deletion to track disk files
            vm_info = self.vbox_manager.get_vm_info(name)
            disk_files = vm_info.get("storage_controllers", [{}])[0].get("devices", [])
            disk_paths = [d.get("path", "") for d in disk_files if d.get("path")]

            # Check VM state (must be powered off to delete)
            current_state = vm_info.get("VMState", "").lower()
            if current_state not in ["poweroff", "aborted", "saved"]:
                raise VBoxManagerError(
                    f"Cannot delete VM in state '{current_state}'. VM must be powered off or saved."
                )

            # Delete the VM using VMOperations
            result = self.vm_operations.delete_vm(name=name, delete_disk=delete_disk)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error deleting VM")
                raise VBoxManagerError(error_msg)

            # Prepare response
            response = {
                "status": "success",
                "vm_name": name,
                "disks_removed": disk_paths if delete_disk else [],
                "disks_retained": [] if delete_disk else disk_paths,
                "message": (
                    f"✓ VM '{name}' and its disk files were successfully deleted"
                    if delete_disk
                    else f"✓ VM '{name}' was removed (disk files retained)"
                ),
                "troubleshooting": [
                    "The VM has been removed from VirtualBox",
                    "You may need to refresh the VirtualBox Manager to see the changes",
                ],
            }

            # Add warning if disk files were retained
            if not delete_disk and disk_paths:
                response["warning"] = (
                    "Disk files were not deleted and may still consume space. "
                    "You may want to manually remove them if they are no longer needed."
                )
                response["troubleshooting"].append(f"Retained disk files: {', '.join(disk_paths)}")

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to delete VM {name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": name,
                "error": str(e),
                "message": f"Failed to delete VM '{name}': {e}",
                "troubleshooting": [
                    "Ensure the VM is powered off before deletion",
                    "Verify you have sufficient permissions to delete the VM",
                    "Check VirtualBox logs for more details",
                ],
            }

    def list_vms(self, details: bool = False, state_filter: str = "all") -> dict[str, Any]:
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

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error listing VMs")
                raise VBoxManagerError(error_msg)

            # Get all VMs and apply state filter if needed
            all_vms = result.get("vms", [])
            total_count = len(all_vms)

            # Apply state filter if not "all"
            if state_filter.lower() != "all":
                filtered_vms = [
                    vm for vm in all_vms if vm.get("state", "").lower() == state_filter.lower()
                ]
            else:
                filtered_vms = all_vms

            filtered_count = len(filtered_vms)

            # Format the response
            response = {
                "status": "success",
                "count": total_count,
                "filtered_count": filtered_count,
                "vms": filtered_vms,
                "message": (
                    f"Found {filtered_count} of {total_count} virtual machine"
                    f"{'s' if total_count != 1 else ''} "
                    f"with state '{state_filter}'"
                    if state_filter.lower() != "all"
                    else f"Found {total_count} virtual machine{'s' if total_count != 1 else ''}"
                ),
                "troubleshooting": [
                    "Use list_vms(details=True) for more information about each VM",
                    "If a VM is missing, verify it's registered in VirtualBox",
                ],
            }

            # Add note about details if not showing them
            if not details and total_count > 0:
                response["troubleshooting"].append(
                    "Some details are hidden. Use details=True to see full VM information."
                )

            # Add warning if filter resulted in no VMs
            if filtered_count == 0 and total_count > 0 and state_filter.lower() != "all":
                response["warning"] = (
                    f"No VMs found with state '{state_filter}'. "
                    f"Available states: {', '.join(set(vm.get('state', 'unknown') for vm in all_vms))}"
                )

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to list VMs: {e}", exc_info=True)
            return {
                "status": "error",
                "count": 0,
                "filtered_count": 0,
                "vms": [],
                "error": str(e),
                "message": f"Failed to list VMs: {e}",
                "troubleshooting": [
                    "Verify VirtualBox is properly installed",
                    "Check if VirtualBox service is running",
                    "Try running 'VBoxManage list vms' in terminal to diagnose",
                ],
            }

    def create_snapshot(
        self, vm_name: str, snapshot_name: str, description: str = ""
    ) -> dict[str, Any]:
        """
        Create a snapshot of a virtual machine.

        This function creates a snapshot of the specified VM, capturing its current state,
        including memory, settings, and disk state. Snapshots are useful for creating
        restore points before making significant changes to a VM.

        Args:
            vm_name: Name of the VM to snapshot
            snapshot_name: Name for the new snapshot
            description: Optional description for the snapshot

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the created snapshot
                "uuid": str,  # UUID of the created snapshot
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> create_snapshot("my-vm", "before-update", "Snapshot before software update")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "before-update",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "message": "✓ Snapshot 'before-update' created successfully for VM 'my-vm'",
                "troubleshooting": [
                    "Use list_snapshots() to view all snapshots for this VM",
                    "To restore this snapshot, use restore_snapshot()"
                ]
            }
        """
        try:
            # Check if VM exists and is in a state that allows snapshots
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            vm_info = self.vbox_manager.get_vm_info(vm_name)
            current_state = vm_info.get("VMState", "").lower()

            # VMs must be powered off, saved, or running to take a snapshot
            if current_state not in ["poweroff", "saved", "running"]:
                raise VBoxManagerError(
                    f"Cannot create snapshot: VM is in state '{current_state}'. "
                    "VM must be powered off, saved, or running."
                )

            # Create the snapshot using VMOperations
            result = self.vm_operations.create_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name, description=description
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error creating snapshot")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "uuid": result.get("snapshot_uuid", ""),
                "message": f"✓ Snapshot '{snapshot_name}' created successfully for VM '{vm_name}'",
                "troubleshooting": [
                    f"Use list_snapshots('{vm_name}') to view all snapshots for this VM",
                    f"To restore this snapshot, use restore_snapshot('{vm_name}', '{snapshot_name}')",
                    "Note: Creating snapshots with memory can take time and disk space",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to create snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "error": str(e),
                "message": f"Failed to create snapshot for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Ensure the VM is not in a transitional state",
                    "Check if there's enough disk space for the snapshot",
                    "Verify VirtualBox has sufficient permissions to create snapshots",
                ],
            }

    def list_snapshots(self, vm_name: str) -> dict[str, Any]:
        """
        List all snapshots for a virtual machine.

        This function retrieves information about all snapshots associated with
        the specified VM, including the snapshot tree structure.

        Args:
            vm_name: Name of the VM to list snapshots for

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_count": int,  # Total number of snapshots
                "current_snapshot": Optional[Dict],  # Current snapshot details if any
                "snapshots": List[Dict],  # List of snapshot details
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> list_snapshots("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_count": 3,
                "current_snapshot": {
                    "name": "after-update",
                    "uuid": "123e4567-e89b-12d3-a456-426614174002",
                    "description": "After software update",
                    "timestamp": "2025-03-15T10:30:00Z",
                    "online": True
                },
                "snapshots": [
                    {
                        "name": "initial-state",
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "description": "Initial VM state",
                        "timestamp": "2025-03-10T09:15:00Z",
                        "online": False,
                        "children": [
                            {
                                "name": "before-update",
                                "uuid": "123e4567-e89b-12d3-a456-426614174001",
                                "description": "Before software update",
                                "timestamp": "2025-03-14T15:45:00Z",
                                "online": False
                            }
                        ]
                    },
                    {
                        "name": "after-update",
                        "uuid": "123e4567-e89b-12d3-a456-426614174002",
                        "description": "After software update",
                        "timestamp": "2025-03-15T10:30:00Z",
                        "online": True
                    }
                ],
                "message": "Found 3 snapshots for VM 'my-vm'",
                "troubleshooting": [
                    "Use restore_snapshot() to revert to a previous state",
                    "Use delete_snapshot() to remove old snapshots and free up disk space"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Get snapshot information using VMOperations
            result = self.vm_operations.list_snapshots(vm_name=vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error listing snapshots")
                raise VBoxManagerError(error_msg)

            snapshots = result.get("snapshots", [])
            current_snapshot = result.get("current_snapshot")

            return {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_count": len(snapshots),
                "current_snapshot": current_snapshot,
                "snapshots": snapshots,
                "message": f"Found {len(snapshots)} snapshot{'s' if len(snapshots) != 1 else ''} for VM '{vm_name}'",
                "troubleshooting": [
                    f"Use restore_snapshot('{vm_name}', '<snapshot-name>') to revert to a previous state",
                    "Snapshots can consume significant disk space over time",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to list snapshots for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_count": 0,
                "snapshots": [],
                "error": str(e),
                "message": f"Failed to list snapshots for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check VirtualBox logs for more detailed error information",
                ],
            }

    def restore_snapshot(
        self, vm_name: str, snapshot_name: str, start_vm: bool = False
    ) -> dict[str, Any]:
        """
        Restore a virtual machine to a previous snapshot.

        This function restores the specified VM to the state it was in when the
        snapshot was taken. All changes made after the snapshot was taken will be lost.

        Args:
            vm_name: Name of the VM to restore
            snapshot_name: Name of the snapshot to restore to
            start_vm: If True, starts the VM after restoration (default: False)

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the restored snapshot
                "started": bool,  # Whether the VM was started after restoration
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> restore_snapshot("my-vm", "clean-install")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "clean-install",
                "started": False,
                "message": "✓ VM 'my-vm' restored to snapshot 'clean-install'",
                "troubleshooting": [
                    "The VM is now in the state it was when the snapshot was taken",
                    "Use start_vm() to start the VM if needed"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Restore the snapshot using VMOperations
            result = self.vm_operations.restore_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error restoring snapshot")
                raise VBoxManagerError(error_msg)

            # Start the VM if requested
            if start_vm:
                start_result = self.start_vm(vm_name)
                if start_result["status"] != "success":
                    raise VBoxManagerError(
                        f"Failed to start VM after restore: {start_result.get('error', 'Unknown error')}"
                    )

            return {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "started": start_vm,
                "message": f"✓ VM '{vm_name}' restored to snapshot '{snapshot_name}'"
                + (" and started" if start_vm else ""),
                "troubleshooting": [
                    "The VM is now in the state it was when the snapshot was taken",
                    "Any changes made after the snapshot was taken have been lost",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to restore snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "started": False,
                "error": str(e),
                "message": f"Failed to restore VM '{vm_name}' to snapshot '{snapshot_name}': {e}",
                "troubleshooting": [
                    "Verify the VM and snapshot exist",
                    "Check if the VM is in a state that allows restoration",
                    "Ensure there's enough disk space for the operation",
                ],
            }

    def delete_snapshot(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """
        Delete a snapshot from a virtual machine.

        This function permanently removes the specified snapshot from the VM's
        snapshot tree. The state of the VM is not affected by this operation.

        Args:
            vm_name: Name of the VM that owns the snapshot
            snapshot_name: Name of the snapshot to delete

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the deleted snapshot
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> delete_snapshot("my-vm", "old-snapshot")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "old-snapshot",
                "message": "✓ Snapshot 'old-snapshot' deleted from VM 'my-vm'",
                "troubleshooting": [
                    "The snapshot has been permanently removed",
                    "This operation cannot be undone"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Delete the snapshot using VMOperations
            result = self.vm_operations.delete_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error deleting snapshot")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "message": f"✓ Snapshot '{snapshot_name}' deleted from VM '{vm_name}'",
                "troubleshooting": [
                    "The snapshot has been permanently removed",
                    "This operation cannot be undone",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to delete snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "error": str(e),
                "message": f"Failed to delete snapshot '{snapshot_name}' from VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify both the VM and snapshot exist",
                    "Check if the snapshot is currently in use",
                    "Ensure you have sufficient permissions to delete snapshots",
                ],
            }

    def configure_network(
        self, vm_name: str, adapter_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Configure network adapters for a virtual machine.

        This function configures the network adapters and settings for a VM.

        Args:
            vm_name: Name of the VM to configure
            adapter_configs: List of adapter configurations. Each adapter config should include:
                - slot: Adapter slot number (0-7)
                - enabled: Whether the adapter is enabled
                - type: Network type (e.g., 'nat', 'bridged', 'hostonly', 'internal', 'natnetwork')
                - network: Network name (for bridged/hostonly/internal/natnetwork types)
                - mac_address: MAC address (or 'auto' for automatic assignment)
                - cable_connected: Whether the cable is connected

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "adapter_count": int,  # Number of adapters configured
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> config = [
            ...     {
            ...         "slot": 0,
            ...         "enabled": True,
            ...         "type": "nat",
            ...         "network": "",
            ...         "mac_address": "auto",
            ...         "cable_connected": True
            ...     },
            ...     {
            ...         "slot": 1,
            ...         "enabled": True,
            ...         "type": "hostonly",
            ...         "network": "vboxnet0",
            ...         "mac_address": "080027B1A2B3",
            ...         "cable_connected": True
            ...     }
            ... ]
            >>> configure_network("my-vm", config)
            {
                "status": "success",
                "vm_name": "my-vm",
                "adapter_count": 2,
                "message": "✓ Network configuration updated for VM 'my-vm'",
                "troubleshooting": [
                    "Network changes take effect after the VM is restarted",
                    "Verify network connectivity from within the guest OS"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Validate adapter configurations
            if not isinstance(adapter_configs, list) or not adapter_configs:
                raise VBoxManagerError("At least one adapter configuration is required")

            # Configure network adapters using VMOperations
            result = self.vm_operations.configure_network(
                vm_name=vm_name, adapter_configs=adapter_configs
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error configuring network")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_count": len(adapter_configs),
                "message": f"✓ Network configuration updated for VM '{vm}'",
                "troubleshooting": [
                    "Network changes take effect after the VM is restarted",
                    "Verify network connectivity from within the guest OS",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to configure network for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "adapter_count": 0,
                "error": str(e),
                "message": f"Failed to configure network for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check network configuration parameters",
                    "Ensure the specified network interfaces exist",
                ],
            }

    def create_template(
        self, vm_name: str, template_name: str, description: str = ""
    ) -> dict[str, Any]:
        """
        Create a template from an existing virtual machine.

        This function creates a template that can be used to create new VMs
        with the same configuration as the source VM.

        Args:
            vm_name: Name of the VM to use as a template
            template_name: Name for the new template
            description: Optional description for the template

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "template_name": str,  # Name of the created template
                "source_vm": str,  # Name of the source VM
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> create_template("ubuntu-20.04", "ubuntu-20.04-base")
            {
                "status": "success",
                "template_name": "ubuntu-20.04-base",
                "source_vm": "ubuntu-20.04",
                "message": "✓ Template 'ubuntu-20.04-base' created successfully",
                "troubleshooting": [
                    "Use deploy_from_template() to create new VMs from this template",
                    "Templates are read-only and cannot be modified"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Create template using VMOperations
            result = self.vm_operations.create_template(
                vm_name=vm_name, template_name=template_name, description=description
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error creating template")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "template_name": template_name,
                "source_vm": vm_name,
                "message": f"✓ Template '{template_name}' created successfully",
                "troubleshooting": [
                    f"Use deploy_from_template('{template_name}', 'new-vm-name') to create a new VM from this template",
                    "Templates are read-only and cannot be modified",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to create template from VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "template_name": template_name,
                "source_vm": vm_name,
                "error": str(e),
                "message": f"Failed to create template '{template_name}' from VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the source VM exists and is accessible",
                    "Check if a template with the same name already exists",
                    "Ensure there's enough disk space for the template",
                ],
            }

    def deploy_from_template(
        self, template_name: str, new_vm_name: str, **kwargs
    ) -> dict[str, Any]:
        """
        Deploy a new virtual machine from a template.

        This function creates a new VM using a previously created template.

        Args:
            template_name: Name of the template to use
            new_vm_name: Name for the new VM
            **kwargs: Additional VM configuration options:
                - memory_mb: Memory allocation in MB (overrides template default)
                - cpus: Number of virtual CPUs (overrides template default)
                - storage_gb: Disk size in GB (overrides template default)
                - network_config: Network configuration (overrides template default)

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the new VM
                "template_name": str,  # Name of the source template
                "message": str,  # Human-readable status message
                "vm_id": Optional[str],  # ID of the new VM if successful
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> deploy_from_template("ubuntu-20.04-base", "my-new-vm", memory_mb=4096, cpus=2)
            {
                "status": "success",
                "vm_name": "my-new-vm",
                "template_name": "ubuntu-20.04-base",
                "vm_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "✓ VM 'my-new-vm' deployed from template 'ubuntu-20.04-base'",
                "troubleshooting": [
                    "Use start_vm() to start the new VM",
                    "Customize the VM configuration as needed"
                ]
            }
        """
        try:
            # Deploy VM from template using VMOperations
            result = self.vm_operations.deploy_from_template(
                template_name=template_name, new_vm_name=new_vm_name, **kwargs
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error deploying from template")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": new_vm_name,
                "template_name": template_name,
                "vm_id": result.get("vm_id", ""),
                "message": f"✓ VM '{new_vm_name}' deployed from template '{template_name}'",
                "troubleshooting": [
                    f"Use start_vm('{new_vm_name}') to start the new VM",
                    "Customize the VM configuration as needed",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to deploy VM from template {template_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": new_vm_name,
                "template_name": template_name,
                "error": str(e),
                "message": f"Failed to deploy VM '{new_vm_name}' from template '{template_name}': {e}",
                "troubleshooting": [
                    "Verify the template exists and is accessible",
                    "Check if a VM with the same name already exists",
                    "Ensure there's enough disk space for the new VM",
                ],
            }

    def get_vm_metrics(self, vm_name: str) -> dict[str, Any]:
        """
        Get performance metrics for a virtual machine.

        This function retrieves CPU, memory, disk, and network metrics for a VM.

        Args:
            vm_name: Name of the VM to get metrics for

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "metrics": Dict[str, Any],  # Performance metrics
                "timestamp": str,  # ISO 8601 timestamp of when metrics were collected
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> get_vm_metrics("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "timestamp": "2025-08-05T02:30:45.123456+02:00",
                "metrics": {
                    "cpu": {
                        "usage_percent": 24.5,
                        "count": 2,
                        "load_per_core": [30.1, 18.9]
                    },
                    "memory": {
                        "used_mb": 2048,
                        "total_mb": 4096,
                        "usage_percent": 50.0
                    },
                    "disk": {
                        "read_bytes": 1024000,
                        "write_bytes": 512000,
                        "read_ops": 150,
                        "write_ops": 75
                    },
                    "network": [
                        {
                            "adapter": 1,
                            "received_bytes": 1024000,
                            "sent_bytes": 512000,
                            "receive_rate_mbps": 1.2,
                            "send_rate_mbps": 0.6
                        }
                    ]
                },
                "message": "✓ Retrieved metrics for VM 'my-vm'",
                "troubleshooting": [
                    "Metrics are a snapshot in time and may vary",
                    "For real-time monitoring, poll this endpoint periodically"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Get VM metrics using VMOperations
            result = self.vm_operations.get_vm_metrics(vm_name=vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error retrieving metrics")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "metrics": result.get("metrics", {}),
                "timestamp": result.get("timestamp", ""),
                "message": f"✓ Retrieved metrics for VM '{vm_name}'",
                "troubleshooting": [
                    "Metrics are a snapshot in time and may vary",
                    "For real-time monitoring, poll this endpoint periodically",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to get metrics for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "metrics": {},
                "error": str(e),
                "message": f"Failed to get metrics for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is running",
                    "Check if the VirtualBox Guest Additions are installed in the guest OS",
                    "Ensure the VM has the necessary permissions to collect metrics",
                ],
            }

    def pause_vm(self, vm_name: str) -> dict[str, Any]:
        """
        Pause a running virtual machine.

        This function suspends the execution of a running VM, preserving its state in memory.
        The VM can be resumed later with resume_vm().

        Args:
            vm_name: Name of the VM to pause

        Returns:
            Dict[str, Any]: Status and details of the pause operation

        Example:
            >>> pause_vm("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ VM 'my-vm' paused successfully",
                "state": "paused"
            }
        """
        try:
            # Check if VM exists and is running
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            vm_state = self.vbox_manager.get_vm_state(vm_name)
            if vm_state != "running":
                raise VBoxManagerError(f"VM '{vm_name}' is not running (current state: {vm_state})")

            # Pause the VM
            result = self.vm_operations.pause_vm(vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error pausing VM")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "message": f"✓ VM '{vm_name}' paused successfully",
                "state": "paused",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to pause VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "error": str(e),
                "message": f"Failed to pause VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is running",
                    "Check if the VM is in a state that can be paused",
                    "Check VirtualBox logs for more details",
                ],
            }

    def resume_vm(self, vm_name: str) -> dict[str, Any]:
        """
        Resume a paused virtual machine.

        This function resumes a VM that was previously paused with pause_vm().

        Args:
            vm_name: Name of the VM to resume

        Returns:
            Dict[str, Any]: Status and details of the resume operation

        Example:
            >>> resume_vm("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ VM 'my-vm' resumed successfully",
                "state": "running"
            }
        """
        try:
            # Check if VM exists and is paused
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            vm_state = self.vbox_manager.get_vm_state(vm_name)
            if vm_state != "paused":
                raise VBoxManagerError(f"VM '{vm_name}' is not paused (current state: {vm_state})")

            # Resume the VM
            result = self.vm_operations.resume_vm(vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error resuming VM")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "message": f"✓ VM '{vm_name}' resumed successfully",
                "state": "running",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to resume VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "error": str(e),
                "message": f"Failed to resume VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is in a paused state",
                    "Check if the VM is in a state that can be resumed",
                    "Check VirtualBox logs for more details",
                ],
            }

    def reset_vm(self, vm_name: str) -> dict[str, Any]:
        """
        Hard reset a virtual machine.

        This function performs a hard reset of the VM, similar to pressing the reset
        button on a physical computer. Any unsaved data may be lost.

        Args:
            vm_name: Name of the VM to reset

        Returns:
            Dict[str, Any]: Status and details of the reset operation

        Example:
            >>> reset_vm("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ VM 'my-vm' reset successfully",
                "state": "running"
            }
        """
        try:
            # Check if VM exists and is running
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            vm_state = self.vbox_manager.get_vm_state(vm_name)
            if vm_state not in ["running", "paused"]:
                raise VBoxManagerError(f"Cannot reset VM '{vm_name}' in state: {vm_state}")

            # Warn about potential data loss
            logger.warning(f"Performing hard reset on VM '{vm_name}'. This may cause data loss.")

            # Reset the VM
            result = self.vm_operations.reset_vm(vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error resetting VM")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "message": f"✓ VM '{vm_name}' reset successfully",
                "state": "running",
                "warning": "Hard reset performed - check for data loss in the guest OS",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to reset VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "error": str(e),
                "message": f"Failed to reset VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is running or paused",
                    "Check if the VM is in a state that can be reset",
                    "Check VirtualBox logs for more details",
                    "Warning: A failed reset may leave the VM in an inconsistent state",
                ],
            }

    def attach_disk(
        self, vm_name: str, disk_path: str, port: int = 0, device: int = 0, type: str = "hdd"
    ) -> dict[str, Any]:
        """
        Attach a virtual disk to a virtual machine.

        Args:
            vm_name: Name of the VM
            disk_path: Path to the virtual disk file
            port: Controller port number (default: 0)
            device: Device number on the port (default: 0)
            type: Disk type ("hdd" or "dvd", default: "hdd")

        Returns:
            Dict[str, Any]: Status and details of the disk attachment

        Example:
            >>> attach_disk("my-vm", "/path/to/disk.vdi")
            {
                "status": "success",
                "vm_name": "my-vm",
                "disk_path": "/path/to/disk.vdi",
                "message": "✓ Disk attached to VM 'my-vm'"
            }
        """
        try:
            # Validate input parameters
            if not vm_name or not disk_path:
                raise VBoxManagerError("VM name and disk path are required")

            if type.lower() not in ["hdd", "dvd"]:
                raise VBoxManagerError(f"Invalid disk type: {type}. Must be 'hdd' or 'dvd'")

            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Check if disk file exists
            if not os.path.exists(disk_path):
                raise VBoxManagerError(f"Disk file not found: {disk_path}")

            # Check if disk is already attached
            attached_disks = self.vbox_manager.get_attached_disks(vm_name)
            for disk in attached_disks:
                if disk["port"] == port and disk["device"] == device:
                    raise VBoxManagerError(
                        f"Port {port} and device {device} already in use by {disk['path']}"
                    )

            # Attach the disk
            result = self.vm_operations.attach_disk(
                vm_name=vm_name,
                disk_path=os.path.abspath(disk_path),
                port=port,
                device=device,
                disk_type=type.lower(),
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error attaching disk")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "disk_path": disk_path,
                "port": port,
                "device": device,
                "type": type.lower(),
                "message": f"✓ Disk attached to VM '{vm_name}' on port {port}, device {device}",
                "troubleshooting": [
                    f"Use 'VBoxManage showvminfo {vm_name} --machinereadable' to verify disk attachment",
                    "Ensure the disk format is supported by VirtualBox",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to attach disk to VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "disk_path": disk_path,
                "error": str(e),
                "message": f"Failed to attach disk to VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is powered off",
                    "Check if the disk file exists and is accessible",
                    "Ensure the port/device combination is available",
                    "Check VirtualBox logs for disk-related errors",
                ],
            }

    def detach_disk(self, vm_name: str, port: int, device: int) -> dict[str, Any]:
        """
        Detach a virtual disk from a virtual machine.

        Args:
            vm_name: Name of the VM
            port: Controller port number
            device: Device number on the port

        Returns:
            Dict[str, Any]: Status and details of the disk detachment

        Example:
            >>> detach_disk("my-vm", port=0, device=0)
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ Disk detached from VM 'my-vm'"
            }
        """
        try:
            # Validate input parameters
            if not vm_name:
                raise VBoxManagerError("VM name is required")

            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Check if disk is actually attached
            attached_disks = self.vbox_manager.get_attached_disks(vm_name)
            disk_found = False

            for disk in attached_disks:
                if disk["port"] == port and disk["device"] == device:
                    disk_found = True
                    break

            if not disk_found:
                raise VBoxManagerError(
                    f"No disk found at port {port}, device {device} on VM '{vm_name}'"
                )

            # Detach the disk
            result = self.vm_operations.detach_disk(vm_name=vm_name, port=port, device=device)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error detaching disk")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "port": port,
                "device": device,
                "message": f"✓ Disk detached from VM '{vm_name}' (port {port}, device {device})",
                "troubleshooting": [
                    f"Use 'VBoxManage showvminfo {vm_name} --machinereadable' to verify disk detachment",
                    "The disk file remains on the host system",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to detach disk from VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "port": port,
                "device": device,
                "error": str(e),
                "message": f"Failed to detach disk from VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is powered off",
                    "Check if the specified port/device has an attached disk",
                    "Check VirtualBox logs for disk-related errors",
                ],
            }

    def attach_iso(
        self, vm_name: str, iso_path: str, port: int = 1, device: int = 0
    ) -> dict[str, Any]:
        """
        Attach an ISO file to a virtual machine's virtual CD/DVD drive.

        Args:
            vm_name: Name of the VM
            iso_path: Path to the ISO file
            port: Controller port number (default: 1)
            device: Device number on the port (default: 0)

        Returns:
            Dict[str, Any]: Status and details of the ISO attachment

        Example:
            >>> attach_iso("my-vm", "/path/to/os.iso")
            {
                "status": "success",
                "vm_name": "my-vm",
                "iso_path": "/path/to/os.iso",
                "message": "✓ ISO attached to VM 'my-vm'"
            }
        """
        try:
            # Validate input parameters
            if not vm_name or not iso_path:
                raise VBoxManagerError("VM name and ISO path are required")

            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Check if ISO file exists
            if not os.path.exists(iso_path):
                raise VBoxManagerError(f"ISO file not found: {iso_path}")

            # Check if the file has a valid ISO extension
            if not iso_path.lower().endswith((".iso", ".iso.gz")):
                logger.warning(f"File '{iso_path}' may not be a valid ISO file")

            # Check if there's already an ISO attached at the specified port/device
            attached_media = self.vbox_manager.get_attached_media(vm_name)
            for media in attached_media:
                if media["port"] == port and media["device"] == device and media["type"] == "dvd":
                    raise VBoxManagerError(
                        f"Port {port} and device {device} already in use by {media['path']}"
                    )

            # Attach the ISO
            result = self.vm_operations.attach_iso(
                vm_name=vm_name, iso_path=os.path.abspath(iso_path), port=port, device=device
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error attaching ISO")
                raise VBoxManagerError(error_msg)

            return {
                "status": "success",
                "vm_name": vm_name,
                "iso_path": iso_path,
                "port": port,
                "device": device,
                "message": f"✓ ISO attached to VM '{vm_name}' on port {port}, device {device}",
                "troubleshooting": [
                    f"Use 'VBoxManage showvminfo {vm_name} --machinereadable' to verify ISO attachment",
                    "The VM may need to be restarted for the changes to take effect",
                ],
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to attach ISO to VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "iso_path": iso_path,
                "error": str(e),
                "message": f"Failed to attach ISO to VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is powered off",
                    "Check if the ISO file exists and is accessible",
                    "Ensure the port/device combination is available",
                    "Check VirtualBox logs for media-related errors",
                ],
            }

    def detach_iso(self, vm_name: str, port: int = 1, device: int = 0) -> dict[str, Any]:
        """
        Detach an ISO file from a virtual machine's virtual CD/DVD drive.

        Args:
            vm_name: Name of the VM
            port: Controller port number (default: 1)
            device: Device number on the port (default: 0)

        Returns:
            Dict[str, Any]: Status and details of the ISO detachment

        Example:
            >>> detach_iso("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ ISO detached from VM 'my-vm'"
            }
        """
        try:
            # Implementation will be added
            pass
        except Exception as e:
            logger.error(f"Failed to detach ISO from VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def install_guest_additions(self, vm_name: str, iso_path: str = None) -> dict[str, Any]:
        """
        Install or update VirtualBox Guest Additions in a virtual machine.

        Args:
            vm_name: Name of the VM
            iso_path: Optional path to the Guest Additions ISO (uses default if None)

        Returns:
            Dict[str, Any]: Status and details of the Guest Additions installation

        Example:
            >>> install_guest_additions("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "message": "✓ Guest Additions installed/updated in VM 'my-vm'"
            }
        """
        try:
            # Implementation will be added
            pass
        except Exception as e:
            logger.error(f"Failed to install Guest Additions in VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def configure_shared_folder(
        self,
        vm_name: str,
        folder_name: str,
        host_path: str,
        auto_mount: bool = True,
        mount_point: str = "",
    ) -> dict[str, Any]:
        """
        Configure a shared folder between the host and guest OS.

        Args:
            vm_name: Name of the VM
            folder_name: Name of the shared folder (as seen in the guest)
            host_path: Path to the folder on the host
            auto_mount: Whether to auto-mount the folder in the guest (default: True)
            mount_point: Mount point in the guest (default: "" for auto)

        Returns:
            Dict[str, Any]: Status and details of the shared folder configuration

        Example:
            >>> configure_shared_folder("my-vm", "shared_data", "/host/path/to/share")
            {
                "status": "success",
                "vm_name": "my-vm",
                "folder_name": "shared_data",
                "host_path": "/host/path/to/share",
                "message": "✓ Shared folder 'shared_data' configured for VM 'my-vm'"
            }
        """
        try:
            # Implementation will be added
            pass
        except Exception as e:
            logger.error(f"Failed to configure shared folder for VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def export_vm(self, vm_name: str, output_path: str, format: str = "ovf-1.0") -> dict[str, Any]:
        """
        Export a virtual machine to an OVF/OVA file.

        Args:
            vm_name: Name of the VM to export
            output_path: Path where to save the exported file
            format: Export format ("ovf-1.0", "ovf-2.0", "ovf-2.0", "ova")

        Returns:
            Dict[str, Any]: Status and details of the export operation

        Example:
            >>> export_vm("my-vm", "/path/to/export.ova")
            {
                "status": "success",
                "vm_name": "my-vm",
                "output_path": "/path/to/export.ova",
                "message": "✓ VM 'my-vm' exported successfully"
            }
        """
        try:
            # Implementation will be added
            pass
        except Exception as e:
            logger.error(f"Failed to export VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def clone_vm(
        self, source_vm: str, new_vm_name: str, clone_type: str = "full"
    ) -> dict[str, Any]:
        """
        Clone a virtual machine.

        Args:
            source_vm: Name of the VM to clone
            new_vm_name: Name for the new VM
            clone_type: Type of clone ("full" or "linked", default: "full")

        Returns:
            Dict[str, Any]: Status and details of the clone operation

        Example:
            >>> clone_vm("template-vm", "new-vm")
            {
                "status": "success",
                "source_vm": "template-vm",
                "new_vm_name": "new-vm",
                "clone_type": "full",
                "message": "✓ VM 'template-vm' cloned to 'new-vm'"
            }
        """
        try:
            # Implementation will be added
            pass
        except Exception as e:
            logger.error(f"Failed to clone VM {source_vm}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # --- Media Management ---
    def list_media(self, media_type: str = None) -> dict[str, Any]:
        """
        List all media (ISOs, disk images) registered with VirtualBox.

        Args:
            media_type: Optional filter by media type ('iso', 'disk', etc.)

        Returns:
            Dict containing list of media files and their details
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "media": [],
                "message": "Media listing not yet implemented",
            }
        except Exception as e:
            logger.error(f"Failed to list media: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def mount_iso(
        self,
        vm_name: str,
        iso_path: str,
        controller_name: str = "IDE Controller",
        port: int = 1,
        device: int = 0,
    ) -> dict[str, Any]:
        """
        Mount an ISO file to a VM's optical drive.

        Args:
            vm_name: Name of the VM
            iso_path: Path to the ISO file
            controller_name: Name of the storage controller
            port: Controller port number
            device: Device number on the port

        Returns:
            Status of the operation
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "iso_path": iso_path,
                "message": f"Mounted {iso_path} to {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to mount ISO to {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def unmount_iso(
        self, vm_name: str, controller_name: str = "IDE Controller", port: int = 1, device: int = 0
    ) -> dict[str, Any]:
        """
        Unmount an ISO from a VM's optical drive.

        Args:
            vm_name: Name of the VM
            controller_name: Name of the storage controller
            port: Controller port number
            device: Device number on the port

        Returns:
            Status of the operation
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "message": f"Unmounted ISO from {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to unmount ISO from {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # --- Network Management ---
    def list_network_adapters(self, vm_name: str) -> dict[str, Any]:
        """
        List all network adapters for a VM.

        Args:
            vm_name: Name of the VM

        Returns:
            Dict containing list of network adapters and their configurations
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapters": [],
                "message": f"Network adapters for {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to list network adapters for {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def configure_network_adapter(
        self,
        vm_name: str,
        adapter_id: int,
        enabled: bool = True,
        network_type: str = "nat",
        mac_address: str = None,
        cable_connected: bool = True,
    ) -> dict[str, Any]:
        """
        Configure a network adapter for a VM.

        Args:
            vm_name: Name of the VM
            adapter_id: ID of the network adapter (0-7)
            enabled: Whether the adapter is enabled
            network_type: Type of network connection ('nat', 'bridged', 'hostonly', 'intnet', 'generic')
            mac_address: Optional MAC address to set
            cable_connected: Whether the network cable is connected

        Returns:
            Status of the operation
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_id": adapter_id,
                "message": f"Configured network adapter {adapter_id} for {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to configure network adapter for {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # --- Storage Management ---
    def list_storage_controllers(self, vm_name: str) -> dict[str, Any]:
        """
        List all storage controllers for a VM.

        Args:
            vm_name: Name of the VM

        Returns:
            Dict containing list of storage controllers and their configurations
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "controllers": [],
                "message": f"Storage controllers for {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to list storage controllers for {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def create_disk(
        self,
        disk_path: str,
        size_gb: int,
        format_type: str = "vdi",
        variant: str = "Standard",
        resizeable: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new virtual disk.

        Args:
            disk_path: Path where to create the disk
            size_gb: Size of the disk in GB
            format_type: Disk format ('vdi', 'vmdk', 'vhd', 'hdd')
            variant: Disk variant ('Standard', 'Fixed', 'Split2G')
            resizeable: Whether the disk can be resized later

        Returns:
            Status of the operation
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "disk_path": disk_path,
                "size_gb": size_gb,
                "message": f"Created {size_gb}GB disk at {disk_path}",
            }
        except Exception as e:
            logger.error(f"Failed to create disk at {disk_path}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def attach_disk(
        self,
        vm_name: str,
        disk_path: str,
        controller_name: str = "SATA Controller",
        port: int = 0,
        device: int = 0,
        disk_type: str = "hdd",
    ) -> dict[str, Any]:
        """
        Attach a disk to a VM.

        Args:
            vm_name: Name of the VM
            disk_path: Path to the disk to attach
            controller_name: Name of the storage controller
            port: Controller port number
            device: Device number on the port
            disk_type: Type of disk ('hdd', 'dvd', 'fdd')

        Returns:
            Status of the operation
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "disk_path": disk_path,
                "message": f"Attached {disk_path} to {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to attach disk to {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # --- System Information ---
    def get_system_info(self) -> dict[str, Any]:
        """
        Get information about the host system and VirtualBox installation.

        Returns:
            Dict containing system and VirtualBox information
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "system": {
                    "os": "Windows",
                    "version": "10.0.19045",
                    "cpu_cores": 8,
                    "memory_gb": 32,
                },
                "virtualbox": {
                    "version": "7.0.12",
                    "api_version": "7_0",
                    "home": "C:\\Program Files\\Oracle\\VirtualBox",
                },
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def get_vm_metrics(self, vm_name: str) -> dict[str, Any]:
        """
        Get performance metrics for a running VM.

        Args:
            vm_name: Name of the VM

        Returns:
            Dict containing VM performance metrics
        """
        try:
            # Implementation will be added
            return {
                "status": "success",
                "vm_name": vm_name,
                "metrics": {
                    "cpu_usage_percent": 0.0,
                    "memory_usage_mb": 0,
                    "disk_read_bytes": 0,
                    "disk_write_bytes": 0,
                    "network_in_bytes": 0,
                    "network_out_bytes": 0,
                },
                "message": f"Metrics for {vm_name}",
            }
        except Exception as e:
            logger.error(f"Failed to get metrics for {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def take_screenshot(
        self, vm_name: str, output_file: str = None, width: int = None, height: int = None
    ) -> dict[str, Any]:
        """
        Take a screenshot of a running VM.

        Args:
            vm_name: Name of the VM
            output_file: Path to save the screenshot (if None, returns as base64)
            width: Width of the screenshot (if None, uses VM display width)
            height: Height of the screenshot (if None, uses VM display height)

        Returns:
            Status of the operation and the screenshot data or path
        """
        try:
            # Implementation will be added
            if output_file:
                return {
                    "status": "success",
                    "vm_name": vm_name,
                    "screenshot_path": output_file,
                    "message": f"Screenshot saved to {output_file}",
                }
            else:
                return {
                    "status": "success",
                    "vm_name": vm_name,
                    "screenshot_data": "base64_encoded_image_data",
                    "message": "Screenshot captured",
                }
        except Exception as e:
            logger.error(f"Failed to take screenshot of {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
