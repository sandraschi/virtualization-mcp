"""
Snapshots - VM snapshot management for testing workflows
Handles create, restore, delete snapshots for rollback patterns
"""

import logging
from datetime import datetime
from typing import Any

from .manager import VBoxManager, VBoxManagerError

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    VM Snapshot management for testing workflows

    Provides Austrian dev efficiency with comprehensive snapshot operations
    for rapid testing cycles and rollback patterns.
    """

    def __init__(self, manager: VBoxManager):
        """
        Initialize snapshot manager

        Args:
            manager: VBoxManager instance
        """
        self.manager = manager

    def create_snapshot(
        self, vm_name: str, snapshot_name: str, description: str = ""
    ) -> dict[str, Any]:
        """
        Create VM snapshot for testing rollback

        Args:
            vm_name: VM name
            snapshot_name: Snapshot identifier
            description: Optional description

        Returns:
            Dict with snapshot creation result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Validate snapshot name
            if not snapshot_name or not snapshot_name.strip():
                raise VBoxManagerError("Snapshot name cannot be empty")

            # Check if snapshot already exists
            existing_snapshots = self.list_snapshots(vm_name)
            if any(snap["name"] == snapshot_name for snap in existing_snapshots):
                raise VBoxManagerError(
                    f"Snapshot '{snapshot_name}' already exists for VM '{vm_name}'"
                )

            # Add timestamp to description if not provided
            if not description:
                description = f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            logger.info(f"Creating snapshot '{snapshot_name}' for VM '{vm_name}'")

            # Create snapshot
            self.manager.run_command(
                ["snapshot", vm_name, "take", snapshot_name, "--description", description]
            )

            # Get snapshot info
            snapshot_info = self._get_snapshot_info(vm_name, snapshot_name)

            result = {
                "success": True,
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "snapshot_info": snapshot_info,
                "message": f"Snapshot '{snapshot_name}' created successfully for VM '{vm_name}'",
            }

            logger.info(f"Successfully created snapshot '{snapshot_name}' for VM '{vm_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to create snapshot '{snapshot_name}' for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating snapshot: {e}")
            raise VBoxManagerError(f"Failed to create snapshot: {str(e)}")

    def restore_snapshot(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """
        Restore VM to specific snapshot state

        Args:
            vm_name: VM name
            snapshot_name: Snapshot to restore

        Returns:
            Dict with restore result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Check if snapshot exists
            existing_snapshots = self.list_snapshots(vm_name)
            if not any(snap["name"] == snapshot_name for snap in existing_snapshots):
                available = [snap["name"] for snap in existing_snapshots]
                raise VBoxManagerError(
                    f"Snapshot '{snapshot_name}' not found for VM '{vm_name}'. "
                    f"Available: {available}"
                )

            # Stop VM if running (required for restore)
            vm_state = self.manager.get_vm_state(vm_name)
            was_running = vm_state == "running"

            if was_running:
                logger.info(f"Stopping VM '{vm_name}' for snapshot restore")
                from .vm_operations import VMOperations

                vm_ops = VMOperations(self.manager)
                vm_ops.stop_vm(vm_name, force=True)

            logger.info(f"Restoring VM '{vm_name}' to snapshot '{snapshot_name}'")

            # Restore snapshot
            self.manager.run_command(["snapshot", vm_name, "restore", snapshot_name])

            result = {
                "success": True,
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "was_running": was_running,
                "restored_at": datetime.now().isoformat(),
                "message": f"VM '{vm_name}' restored to snapshot '{snapshot_name}'",
            }

            logger.info(f"Successfully restored VM '{vm_name}' to snapshot '{snapshot_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to restore snapshot '{snapshot_name}' for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error restoring snapshot: {e}")
            raise VBoxManagerError(f"Failed to restore snapshot: {str(e)}")

    def delete_snapshot(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """
        Delete snapshot to save disk space

        Args:
            vm_name: VM name
            snapshot_name: Snapshot to delete

        Returns:
            Dict with deletion result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Check if snapshot exists
            existing_snapshots = self.list_snapshots(vm_name)
            if not any(snap["name"] == snapshot_name for snap in existing_snapshots):
                raise VBoxManagerError(f"Snapshot '{snapshot_name}' not found for VM '{vm_name}'")

            logger.info(f"Deleting snapshot '{snapshot_name}' for VM '{vm_name}'")

            # Delete snapshot
            self.manager.run_command(["snapshot", vm_name, "delete", snapshot_name])

            result = {
                "success": True,
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "deleted_at": datetime.now().isoformat(),
                "message": f"Snapshot '{snapshot_name}' deleted for VM '{vm_name}'",
            }

            logger.info(f"Successfully deleted snapshot '{snapshot_name}' for VM '{vm_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to delete snapshot '{snapshot_name}' for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting snapshot: {e}")
            raise VBoxManagerError(f"Failed to delete snapshot: {str(e)}")

    def list_snapshots(self, vm_name: str) -> list[dict[str, Any]]:
        """
        List all snapshots for a VM

        Args:
            vm_name: VM name

        Returns:
            List of snapshot info dicts
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Get snapshot list
            result = self.manager.run_command(["snapshot", vm_name, "list", "--machinereadable"])

            return self._parse_snapshots_list(result["output"])

        except VBoxManagerError as e:
            if "no snapshots" in str(e).lower() or "does not have" in str(e).lower():
                # No snapshots exist - return empty list
                return []
            logger.error(f"Failed to list snapshots for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing snapshots: {e}")
            raise VBoxManagerError(f"Failed to list snapshots: {str(e)}")

    def _parse_snapshots_list(self, output: str) -> list[dict[str, Any]]:
        """Parse VBoxManage snapshot list output"""
        snapshots = []
        current_snapshot = {}

        for line in output.split("\n"):
            if "=" in line and line.strip():
                key, value = line.split("=", 1)
                value = value.strip('"')

                if key.startswith("SnapshotName"):
                    if current_snapshot:
                        snapshots.append(current_snapshot)
                    current_snapshot = {"name": value}
                elif key.startswith("SnapshotUUID") and current_snapshot:
                    current_snapshot["uuid"] = value
                elif key.startswith("SnapshotDescription") and current_snapshot:
                    current_snapshot["description"] = value
                elif key.startswith("SnapshotTimeStamp") and current_snapshot:
                    current_snapshot["timestamp"] = value

        # Add last snapshot if exists
        if current_snapshot:
            snapshots.append(current_snapshot)

        return snapshots

    def _get_snapshot_info(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """Get detailed info about specific snapshot"""
        snapshots = self.list_snapshots(vm_name)
        for snapshot in snapshots:
            if snapshot["name"] == snapshot_name:
                return snapshot
        return {}

    def rollback_and_restart(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """
        Atomic rollback to snapshot and restart VM

        Args:
            vm_name: VM name
            snapshot_name: Snapshot to restore

        Returns:
            Dict with combined operation result
        """
        try:
            logger.info(
                f"Starting rollback and restart for VM '{vm_name}' to snapshot '{snapshot_name}'"
            )

            # Restore snapshot
            restore_result = self.restore_snapshot(vm_name, snapshot_name)

            # Start VM
            from .vm_operations import VMOperations

            vm_ops = VMOperations(self.manager)
            start_result = vm_ops.start_vm(vm_name, headless=True)

            result = {
                "success": True,
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "restore_result": restore_result,
                "start_result": start_result,
                "completed_at": datetime.now().isoformat(),
                "message": f"VM '{vm_name}' rolled back to '{snapshot_name}' and restarted",
            }

            logger.info(f"Successfully completed rollback and restart for VM '{vm_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed rollback and restart for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rollback and restart: {e}")
            raise VBoxManagerError(f"Failed rollback and restart: {str(e)}")

    def get_current_snapshot(self, vm_name: str) -> dict[str, Any] | None:
        """
        Get the current snapshot (if VM is in a snapshot state)

        Args:
            vm_name: VM name

        Returns:
            Current snapshot info or None
        """
        try:
            vm_info = self.manager.get_vm_info(vm_name)
            current_snapshot_uuid = vm_info.get("CurrentSnapshotUUID")

            if current_snapshot_uuid and current_snapshot_uuid != "":
                snapshots = self.list_snapshots(vm_name)
                for snapshot in snapshots:
                    if snapshot.get("uuid") == current_snapshot_uuid:
                        return snapshot

            return None

        except Exception as e:
            logger.warning(f"Failed to get current snapshot for VM '{vm_name}': {e}")
            return None

    def clone_vm(
        self,
        source_vm: str,
        target_vm: str,
        linked: bool = True,
        snapshot_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Clone VM for testing (linked clones save space)

        Args:
            source_vm: Source VM name
            target_vm: Target VM name
            linked: Create linked clone (saves disk space)
            snapshot_name: Clone from specific snapshot

        Returns:
            Dict with clone result
        """
        try:
            if not self.manager.vm_exists(source_vm):
                raise VBoxManagerError(f"Source VM '{source_vm}' not found")

            if self.manager.vm_exists(target_vm):
                raise VBoxManagerError(f"Target VM '{target_vm}' already exists")

            # Validate target VM name
            if not self.manager.validate_vm_name(target_vm):
                raise VBoxManagerError(f"Invalid target VM name: '{target_vm}'")

            logger.info(f"Cloning VM '{source_vm}' to '{target_vm}' (linked={linked})")

            cmd = ["clonevm", source_vm, "--name", target_vm, "--register"]

            # Add clone options
            if linked:
                cmd.extend(["--mode", "link"])
            else:
                cmd.extend(["--mode", "all"])

            # Clone from specific snapshot if specified
            if snapshot_name:
                snapshots = self.list_snapshots(source_vm)
                if not any(snap["name"] == snapshot_name for snap in snapshots):
                    raise VBoxManagerError(f"Snapshot '{snapshot_name}' not found in source VM")
                cmd.extend(["--snapshot", snapshot_name])

            # Execute clone
            self.manager.run_command(cmd)

            # Get cloned VM info
            vm_info = self.manager.get_vm_info(target_vm)

            result = {
                "success": True,
                "source_vm": source_vm,
                "target_vm": target_vm,
                "linked_clone": linked,
                "from_snapshot": snapshot_name,
                "vm_info": vm_info,
                "cloned_at": datetime.now().isoformat(),
                "message": f"VM '{source_vm}' cloned to '{target_vm}' successfully",
            }

            logger.info(f"Successfully cloned VM '{source_vm}' to '{target_vm}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to clone VM '{source_vm}' to '{target_vm}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error cloning VM: {e}")
            raise VBoxManagerError(f"Failed to clone VM: {str(e)}")
