"""
VirtualBox Compatibility Adapter

This module provides a compatibility layer between the existing VBoxManager class
and our new vbox_compat module, allowing for a smooth transition.
"""

import logging
from datetime import datetime
from typing import Any

# Import our new compatibility layer
from ..vbox_compat import VBoxManage, VirtualBoxError

logger = logging.getLogger(__name__)


class VBoxManagerError(Exception):
    """Custom exception for VirtualBox operations"""

    def __init__(self, message: str, command: list[str] = None, return_code: int = None):
        super().__init__(message)
        self.command = command
        self.return_code = return_code


class VBoxManager:
    """
    Adapter class that provides the same interface as the original VBoxManager
    but uses our new vbox_compat module under the hood.
    """

    def __init__(self, vboxmanage_path: str = None):
        """
        Initialize the VBoxManager adapter.

        Args:
            vboxmanage_path: Optional path to VBoxManage executable.
        """
        self.vbox = VBoxManage()
        self.vboxmanage_path = vboxmanage_path or self._find_vboxmanage()
        self._validate_vboxmanage()

    def _find_vboxmanage(self) -> str:
        """Find VBoxManage executable (stub for compatibility)."""
        return "VBoxManage"

    def _validate_vboxmanage(self) -> None:
        """Validate that VBoxManage is accessible."""
        try:
            self.vbox.version
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to access VBoxManage: {e}")

    def vm_exists(self, vm_name: str) -> bool:
        """Check if a VM with the given name exists."""
        try:
            vms = self.list_vms()
            return any(vm["name"] == vm_name for vm in vms)
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to check if VM exists: {e}")

    def _execute(self, command: list[str], parse_json: bool = False) -> Any:
        """
        Execute a VBoxManage command.

        Args:
            command: The command and its arguments as a list
            parse_json: If True, parse the output as JSON

        Returns:
            The command output as a string or parsed JSON

        Raises:
            VBoxManagerError: If the command fails
        """
        try:
            # Convert the command to our new format
            cmd_str = (
                " ".join(command[1:])
                if command and command[0] == "VBoxManage"
                else " ".join(command)
            )
            return self.vbox._run_command(cmd_str, parse_json=parse_json)
        except VirtualBoxError as e:
            raise VBoxManagerError(str(e), command=command) from e

    def get_vm_state(self, vm_name: str) -> str:
        """
        Get the current state of a VM.

        Args:
            vm_name: Name or UUID of the VM

        Returns:
            str: VM state (e.g., "running", "poweroff", "paused", "saved", "aborted")
        """
        try:
            vm_info = self.get_vm_info(vm_name)
            return self._normalize_vm_state(vm_info.get("VMState", "poweroff"))
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to get VM state: {e}")

    def _normalize_vm_state(self, state: str) -> str:
        """Normalize VM state to match the expected format."""
        state = str(state).lower()

        # Map common states to standard values
        state_map = {
            "poweroff": "poweroff",
            "poweredoff": "poweroff",
            "running": "running",
            "paused": "paused",
            "saved": "saved",
            "aborted": "aborted",
            "starting": "starting",
            "stopping": "stopping",
            "saving": "saving",
            "restoring": "restoring",
        }

        return state_map.get(state, "unknown")

    def _find_vboxmanage(self) -> str:
        """Find VBoxManage executable (stub for compatibility)."""
        return "VBoxManage"

    def _validate_vboxmanage(self) -> None:
        """Validate that VBoxManage is accessible (stub for compatibility)."""
        try:
            self.vbox.version
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to access VBoxManage: {e}")

    def list_vms(self, **kwargs) -> list[dict[str, Any]]:
        """
        List all registered VMs.

        Args:
            **kwargs: Additional filters (e.g., running_only=True)

        Returns:
            List of VM information dictionaries
        """
        try:
            vms = self.vbox.list_vms(verbose=True)

            # Convert to the expected format
            result = []
            for vm in vms:
                vm_info = {
                    "name": vm.get("name", ""),
                    "uuid": vm.get("uuid", ""),
                    "state": self._normalize_vm_state(vm.get("state", "poweroff")),
                    "ostype": vm.get("ostype", "Other"),
                    "memory": int(vm.get("memory", 0)) // 1024,  # Convert to MB
                    "cpus": int(vm.get("cpus", 1)),
                }

                # Apply filters if provided
                if kwargs.get("running_only") and vm_info["state"] != "running":
                    continue

                result.append(vm_info)

            return result
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to list VMs: {e}")

    def get_vm_info(self, vm_name: str) -> dict[str, Any]:
        """
        Get detailed information about a VM.

        Args:
            vm_name: Name or UUID of the VM

        Returns:
            Dictionary containing VM information
        """
        try:
            # Get basic VM info
            info = self.vbox.get_vm_info(vm_name)

            # Get additional info using showvminfo
            result = self._execute(["showvminfo", "--machinereadable", vm_name])

            # Parse the machine-readable output
            for line in result.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    info[key.lower()] = value.strip('"')

            return info
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to get VM info: {e}")

    def get_vm_config(self, vm_name: str) -> dict[str, Any]:
        """
        Get the configuration of a VM.

        Args:
            vm_name: Name or UUID of the VM

        Returns:
            Dictionary containing VM configuration
        """
        try:
            # Get detailed VM info
            vm_info = self.get_vm_info(vm_name)

            # Extract relevant configuration
            config = {
                "name": vm_info.get("name", ""),
                "ostype": vm_info.get("ostype", "Other"),
                "memory": int(vm_info.get("memory", 0)) // 1024,  # Convert to MB
                "cpus": int(vm_info.get("cpus", 1)),
                "vram": int(vm_info.get("vram", 16)),  # Default to 16MB
                "firmware": vm_info.get("firmware", "BIOS"),
                "chipset": vm_info.get("chipset", "ICH9"),
                "ioapic": vm_info.get("ioapic", "on") == "on",
                "pae": vm_info.get("pae", "off") == "on",
                "longmode": vm_info.get("longmode", "on") == "on",
                "hpet": vm_info.get("hpet", "off") == "on",
                "nestedpaging": vm_info.get("nestedpaging", "on") == "on",
                "largepages": vm_info.get("largepages", "off") == "on",
                "vtxvpid": vm_info.get("vtxvpid", "on") == "on",
                "vtxux": vm_info.get("vtxux", "on") == "on",
            }

            return config
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to get VM config: {e}")

    def start_vm(self, vm_name: str, headless: bool = False, **kwargs) -> bool:
        """
        Start a VM.

        Args:
            vm_name: Name or UUID of the VM to start
            headless: If True, start in headless mode
            **kwargs: Additional options (e.g., type='headless'|'gui'|'sdl')

        Returns:
            True if the VM was started successfully
        """
        try:
            # Determine the start type
            start_type = "headless" if headless else "gui"
            if "type" in kwargs:
                start_type = kwargs["type"]

            # Start the VM with the specified type
            self.vbox._run_command(f"startvm {vm_name} --type {start_type}")
            return True
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to start VM: {e}")

    def stop_vm(self, vm_name: str, force: bool = False, **kwargs) -> bool:
        """
        Stop a running VM.

        Args:
            vm_name: Name or UUID of the VM to stop
            force: If True, force stop the VM (equivalent to power off)
            **kwargs: Additional options (e.g., save_state=True)

        Returns:
            True if the VM was stopped successfully
        """
        try:
            if kwargs.get("save_state"):
                # Save the VM state instead of powering off
                self.vbox._run_command(f"controlvm {vm_name} savestate")
            elif force:
                # Force power off
                self.vbox._run_command(f"controlvm {vm_name} poweroff")
            else:
                # Send ACPI power button event (graceful shutdown)
                self.vbox._run_command(f"controlvm {vm_name} acpipowerbutton")

            return True
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to stop VM: {e}")

    def create_vm(
        self, name: str = None, ostype: str = None, memory: int = None, cpus: int = None, **kwargs
    ) -> dict[str, Any]:
        """
        Create a new VM.

        This method supports both named and positional parameters for compatibility.

        Args:
            name: Name of the new VM (can be passed as first positional argument or as keyword)
            ostype: OS type identifier (e.g., 'Windows11_64')
            memory: Memory in MB
            cpus: Number of CPUs
            **kwargs: Additional VM configuration options or overrides for positional parameters
                - disk_size_mb: Size of the boot disk in MB (default: 32768)
                - vram_mb: Video memory in MB (default: 128)
                - firmware: 'bios' or 'efi' (default: 'bios')
                - chipset: 'ich9' or 'piix3' (default: 'ich9')
                - ioapic: Enable I/O APIC (default: True)
                - nestedpaging: Enable nested paging (default: True)
                - vtxvpid: Enable VT-x/AMD-v (default: True)

        Returns:
            Dictionary containing information about the created VM

        Note:
            For backward compatibility, the first four parameters can be passed as positional arguments:
            create_vm(name, ostype, memory, cpus, **kwargs)
        """
        # Handle both named and positional parameters
        name = name or kwargs.get("name")
        ostype = ostype or kwargs.get("ostype")
        memory = memory or kwargs.get("memory")
        cpus = cpus or kwargs.get("cpus")

        # Validate required parameters
        if not all([name, ostype, memory is not None, cpus is not None]):
            raise VBoxManagerError(
                "Missing required parameters. Name, ostype, memory, and cpus are required."
            )

        try:
            # Default VM settings
            disk_size_mb = kwargs.get("disk_size_mb", 32768)  # 32GB default
            vram_mb = kwargs.get("vram_mb", 128)

            # Create the VM
            self.vbox._run_command(f'createvm --name "{name}" --ostype {ostype} --register')

            # Set basic system properties
            self.vbox._run_command(
                f'storagectl "{name}" --name "SATA Controller" --add sata --controller IntelAHCI'
            )
            self.vbox._run_command(
                f'modifyvm "{name}" --memory {memory} --vram {vram_mb} --cpus {cpus}'
            )

            # Set firmware and chipset
            firmware = kwargs.get("firmware", "bios").lower()
            if firmware == "efi":
                self.vbox._run_command(f'modifyvm "{name}" --firmware efi')

            chipset = kwargs.get("chipset", "ich9").lower()
            self.vbox._run_command(f'modifyvm "{name}" --chipset {chipset}')

            # Set CPU features
            if kwargs.get("ioapic", True):
                self.vbox._run_command(f'modifyvm "{name}" --ioapic on')

            if kwargs.get("nestedpaging", True):
                self.vbox._run_command(f'modifyvm "{name}" --nestedpaging on')

            if kwargs.get("vtxvpid", True):
                self.vbox._run_command(f'modifyvm "{name}" --vtxvpid on')

            # Add a boot disk if requested
            if disk_size_mb > 0:
                # Create a disk image
                disk_path = f'"{name}_disk.vdi"'
                self.vbox._run_command(
                    f"createhd --filename {disk_path} --size {disk_size_mb // 1024} --variant Standard"
                )

                # Attach the disk to the VM
                self.vbox._run_command(
                    f'storageattach "{name}" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium {disk_path}'
                )

            # Get the VM UUID for the return value
            vm_info = self.get_vm_info(name)

            return {
                "name": name,
                "uuid": vm_info.get("uuid", ""),
                "ostype": ostype,
                "memory": memory,
                "cpus": cpus,
                "state": "poweroff",
                "vram": vram_mb,
                "firmware": firmware,
                "chipset": chipset,
                "ioapic": kwargs.get("ioapic", True),
                "nestedpaging": kwargs.get("nestedpaging", True),
                "vtxvpid": kwargs.get("vtxvpid", True),
            }
        except VirtualBoxError as e:
            # Clean up partially created VM on error
            try:
                if self.vm_exists(name):
                    self.vbox._run_command(f'unregistervm "{name}" --delete')
            except Exception:
                pass

            raise VBoxManagerError(f"Failed to create VM: {e}")

    def delete_vm(self, vm_name: str, delete_disks: bool = False) -> bool:
        """
        Delete a VM.

        Args:
            vm_name: Name or UUID of the VM to delete
            delete_disks: If True, also delete associated disk images

        Returns:
            True if the VM was deleted successfully
        """
        try:
            # First, ensure the VM is powered off
            state = self.get_vm_state(vm_name).lower()
            if state == "running":
                self.stop_vm(vm_name, force=True)

            # Get disk info before deleting if we need to clean up
            disks_to_delete = []
            if delete_disks:
                vm_info = self.get_vm_info(vm_name)
                # Look for disk attachments in storage controllers
                for i in range(10):  # Check up to 10 storage controllers
                    try:
                        # Get the storage controller name
                        ctrl_name = f"storagecontrollername{i}"
                        if ctrl_name in vm_info:
                            # Find all disks attached to this controller
                            for port in range(0, 30):  # Check up to 30 ports
                                disk_key = f"sata-{vm_info[ctrl_name]}-{port}-0"
                                if disk_key in vm_info and "ImageUUID" in vm_info[disk_key]:
                                    disks_to_delete.append(vm_info[disk_key])
                    except (KeyError, IndexError):
                        break

            # Delete the VM
            self.vbox._run_command(f'unregistervm "{vm_name}" --delete')

            # Delete associated disks if requested
            if delete_disks and disks_to_delete:
                for disk in disks_to_delete:
                    try:
                        self.vbox._run_command(f"closemedium disk {disk} --delete")
                    except VirtualBoxError:
                        # Ignore errors when deleting disks that are already gone
                        pass

            return True
        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to delete VM: {e}")

    def execute_in_vm(self, vm_name: str, command: list[str], **kwargs) -> str:
        """
        Execute a command inside a running VM using guest control.

        Args:
            vm_name: Name or UUID of the VM
            command: Command to execute (first element is the command, rest are args)
            **kwargs: Additional options:
                - username: Guest OS username (required)
                - password: Guest OS password (required)
                - wait: Wait for command to complete (default: True)
                - timeout_ms: Timeout in milliseconds (default: 30000)
                - env: Dict of environment variables to set
                - cwd: Working directory

        Returns:
            Command output as string

        Note:
            Requires Guest Additions to be installed in the VM
        """
        try:
            if not command:
                raise ValueError("No command specified")

            # Get required parameters
            username = kwargs.get("username")
            password = kwargs.get("password")
            wait = kwargs.get("wait", True)
            timeout_ms = kwargs.get("timeout_ms", 30000)

            if not username or not password:
                raise ValueError("Both username and password are required for guest control")

            # Build the guestcontrol command
            cmd_parts = [
                "guestcontrol",
                vm_name,
                "execute",
                "--username",
                username,
                "--password",
                password,
                "--wait-exe",
                str(timeout_ms // 1000),  # Convert to seconds
                "--timeout",
                str(timeout_ms // 1000),
                "--",
                command[0],  # The command to execute
            ]

            # Add arguments if any
            if len(command) > 1:
                cmd_parts.extend(command[1:])

            # Set environment variables if provided
            env = kwargs.get("env", {})
            for key, value in env.items():
                cmd_parts.extend(["--putenv", f"{key}={value}"])

            # Set working directory if provided
            cwd = kwargs.get("cwd")
            if cwd:
                cmd_parts.extend(["--cwd", cwd])

            # Execute the command
            return self.vbox._run_command(
                " ".join(f'"{part}"' if " " in str(part) else str(part) for part in cmd_parts)
            )

        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to execute command in VM: {e}")

    def take_snapshot(
        self, vm_name: str, snapshot_name: str, description: str = "", **kwargs
    ) -> dict[str, Any]:
        """
        Take a snapshot of a VM.

        Args:
            vm_name: Name or UUID of the VM
            snapshot_name: Name for the snapshot
            description: Optional description
            **kwargs: Additional options:
                - pause_vm: Whether to pause the VM during snapshot (default: True)
                - live: Whether to take a live snapshot without pausing (default: False)

        Returns:
            Dictionary containing snapshot information including UUID

        Raises:
            VBoxManagerError: If snapshot creation fails
        """
        try:
            # Build the snapshot command
            cmd = ["snapshot", vm_name, "take", snapshot_name]

            # Add description if provided
            if description:
                cmd.extend(["--description", f'"{description}"'])

            # Add pause/live options
            if kwargs.get("live", False):
                cmd.append("--live")
            elif kwargs.get("pause_vm", True):
                cmd.append("--pause")
            else:
                cmd.append("--unpause")

            # Execute the snapshot command
            output = self.vbox._run_command(" ".join(cmd))

            # Extract the snapshot UUID from the output
            snapshot_uuid = None
            for line in output.splitlines():
                if "Snapshot taken" in line and "UUID:" in line:
                    snapshot_uuid = line.split("UUID:")[-1].strip()
                    break

            if not snapshot_uuid:
                raise VBoxManagerError("Failed to extract snapshot UUID from output")

            return {
                "name": snapshot_name,
                "uuid": snapshot_uuid,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "vm_name": vm_name,
            }

        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to take snapshot: {e}")

    def restore_snapshot(
        self,
        vm_name: str,
        snapshot_name: str | None = None,
        snapshot_uuid: str | None = None,
        **kwargs,
    ) -> bool:
        """
        Restore a VM to a previous snapshot.

        Args:
            vm_name: Name or UUID of the VM
            snapshot_name: Name of the snapshot to restore (either name or UUID must be provided)
            snapshot_uuid: UUID of the snapshot to restore (either name or UUID must be provided)
            **kwargs: Additional options:
                - start_vm: Whether to start the VM after restore (default: False)
                - reset_network: Whether to reset network adapters (default: True)

        Returns:
            True if the snapshot was restored successfully

        Raises:
            VBoxManagerError: If snapshot restore fails
            ValueError: If neither snapshot name nor UUID is provided
        """
        if not snapshot_name and not snapshot_uuid:
            raise ValueError("Either snapshot_name or snapshot_uuid must be provided")

        try:
            # First, ensure the VM is powered off
            state = self.get_vm_state(vm_name).lower()
            if state == "running":
                self.stop_vm(vm_name, force=True)

            # Build the snapshot restore command
            snapshot_id = snapshot_uuid or f'"{snapshot_name}"'
            self.vbox._run_command(f"snapshot {vm_name} restore {snapshot_id}")

            # Start the VM if requested
            if kwargs.get("start_vm", False):
                self.start_vm(vm_name)

            return True

        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to restore snapshot: {e}")

    def list_snapshots(self, vm_name: str) -> list[dict[str, Any]]:
        """
        List all snapshots for a VM.

        Args:
            vm_name: Name or UUID of the VM

        Returns:
            List of snapshot dictionaries with name, UUID, and other metadata

        Raises:
            VBoxManagerError: If listing snapshots fails
        """
        try:
            output = self.vbox._run_command(f"snapshot {vm_name} list --machinereadable")

            snapshots = []
            current_snapshot = {}

            # Parse the machine-readable output
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith("SnapshotName"):
                    if current_snapshot:
                        snapshots.append(current_snapshot)
                    current_snapshot = {"name": line.split("=")[1].strip('"')}
                elif line.startswith("SnapshotUUID"):
                    current_snapshot["uuid"] = line.split("=")[1].strip('"')
                elif line.startswith("SnapshotDescription"):
                    current_snapshot["description"] = line.split("=")[1].strip('"')
                elif line.startswith("SnapshotTimeStamp"):
                    current_snapshot["timestamp"] = line.split("=")[1].strip('"')

            # Add the last snapshot
            if current_snapshot:
                snapshots.append(current_snapshot)

            return snapshots

        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to list snapshots: {e}")

    def delete_snapshot(
        self, vm_name: str, snapshot_name: str | None = None, snapshot_uuid: str | None = None
    ) -> bool:
        """
        Delete a snapshot.

        Args:
            vm_name: Name or UUID of the VM
            snapshot_name: Name of the snapshot to delete (either name or UUID must be provided)
            snapshot_uuid: UUID of the snapshot to delete (either name or UUID must be provided)

        Returns:
            True if the snapshot was deleted successfully

        Raises:
            VBoxManagerError: If snapshot deletion fails
            ValueError: If neither snapshot name nor UUID is provided
        """
        if not snapshot_name and not snapshot_uuid:
            raise ValueError("Either snapshot_name or snapshot_uuid must be provided")

        try:
            snapshot_id = snapshot_uuid or f'"{snapshot_name}"'
            self.vbox._run_command(f"snapshot {vm_name} delete {snapshot_id}")
            return True

        except VirtualBoxError as e:
            raise VBoxManagerError(f"Failed to delete snapshot: {e}")


# For backward compatibility
def get_vbox_manager() -> VBoxManager:
    """
    Get a VBoxManager instance (compatibility function).

    Returns:
        VBoxManager instance
    """
    return VBoxManager()
