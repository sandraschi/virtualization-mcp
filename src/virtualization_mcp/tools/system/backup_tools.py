"""Backup tools for managing VM backups in virtualization-mcp."""

import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages VM backups."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the backup manager."""
        self.config = config or {}
        self.backup_dir = Path(self.config.get("backup_dir", "./backups"))
        self.retention_days = self.config.get("retention_days", 30)
        self.max_backups = self.config.get("max_backups", 10)

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Active backup tasks
        self.active_tasks: dict[str, asyncio.Task] = {}

    async def create_backup(
        self, vm_name: str, name: str | None = None, description: str = ""
    ) -> dict[str, Any]:
        """Create a backup of a VM.

        Args:
            vm_name: Name of the VM to back up
            name: Optional name for the backup (defaults to vm_name_timestamp)
            description: Optional description for the backup

        Returns:
            Dictionary with backup status and metadata
        """
        if not name:
            name = f"{vm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if name in self.active_tasks:
            return {"status": "error", "error": f"Backup task for '{name}' already in progress"}

        # Start backup in background
        task = asyncio.create_task(self._create_backup(vm_name, name, description))
        self.active_tasks[name] = task

        # Clean up task when done
        task.add_done_callback(lambda t, n=name: self.active_tasks.pop(n, None))

        return {
            "status": "started",
            "backup_name": name,
            "vm_name": vm_name,
            "start_time": datetime.utcnow().isoformat(),
        }

    async def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup metadata dictionaries
        """
        backups = []
        for backup_dir in self.backup_dir.glob("*"):
            if not backup_dir.is_dir():
                continue

            # Get metadata
            metadata = self._read_metadata(backup_dir)
            if not metadata:
                continue

            backups.append(
                {
                    "name": backup_dir.name,
                    "vm_name": metadata.get("vm_name", "unknown"),
                    "created_at": metadata.get("created_at", ""),
                    "description": metadata.get("description", ""),
                    "size": self._get_dir_size(backup_dir),
                }
            )

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    async def delete_backup(self, backup_name: str) -> dict[str, Any]:
        """Delete a backup.

        Args:
            backup_name: Name of the backup to delete

        Returns:
            Status of the deletion
        """
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists() or not backup_path.is_dir():
            return {"status": "error", "error": f"Backup '{backup_name}' not found"}

        try:
            shutil.rmtree(backup_path)
            return {"status": "success", "name": backup_name}
        except Exception as e:
            return {"status": "error", "error": f"Failed to delete backup: {str(e)}"}

    async def _create_backup(
        self, vm_name: str, backup_name: str, description: str = ""
    ) -> dict[str, Any]:
        """Internal method to create a backup.

        Args:
            vm_name: Name of the VM to back up
            backup_name: Name for the backup
            description: Optional description for the backup

        Returns:
            Dictionary with backup status and metadata
        """
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        metadata = {
            "vm_name": vm_name,
            "backup_name": backup_name,
            "created_at": datetime.utcnow().isoformat(),
            "description": description,
            "status": "in_progress",
        }

        try:
            # Save metadata
            self._write_metadata(backup_path, metadata)

            # TODO: Implement actual backup logic
            # This is a placeholder implementation
            await asyncio.sleep(5)  # Simulate backup time

            # Update metadata
            metadata.update({"status": "completed", "completed_at": datetime.utcnow().isoformat()})
            self._write_metadata(backup_path, metadata)

            return {"status": "completed", "backup_name": backup_name}

        except Exception as e:
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            self._write_metadata(backup_path, metadata)

            return {"status": "error", "error": str(e)}

    def _write_metadata(self, backup_path: Path, metadata: dict[str, Any]) -> None:
        """Write metadata to a backup directory."""
        metadata_path = backup_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def _read_metadata(self, backup_path: Path) -> dict[str, Any] | None:
        """Read metadata from a backup directory."""
        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path) as f:
                return json.load(f)
        except Exception:
            return None

    def _get_dir_size(self, path: Path) -> int:
        """Calculate the total size of a directory."""
        total_size = 0
        for file in path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size


# Create a singleton instance
backup_manager = BackupManager()

# Export the tool functions
create_backup = backup_manager.create_backup
list_backups = backup_manager.list_backups
delete_backup = backup_manager.delete_backup
