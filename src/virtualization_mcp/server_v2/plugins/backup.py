"""Backup plugin for virtualization-mcp."""
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks, status

from virtualization_mcp.server_v2.plugins.base import BasePlugin
from virtualization_mcp.server_v2.plugins import register_plugin

logger = logging.getLogger(__name__)

@register_plugin("backup")
class BackupPlugin(BasePlugin):
    """Backup plugin for managing VM backups."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the backup plugin."""
        super().__init__(config)
        
        # Configuration
        self.backup_dir = Path(config.get("backup_dir", "./backups"))
        self.retention_days = config.get("retention_days", 30)
        self.max_backups = config.get("max_backups", 10)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Active backup tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self) -> None:
        """Set up API routes for backup operations."""
        @self.router.post("/vms/{vm_name}/backup")
        async def create_backup(
            vm_name: str,
            background_tasks: BackgroundTasks,
            name: str = "",
            description: str = ""
        ) -> Dict[str, Any]:
            """Create a backup of a VM."""
            if not name:
                name = f"{vm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if name in self.active_tasks:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Backup task for '{name}' already in progress"
                )
            
            # Start backup in background
            task = asyncio.create_task(self._create_backup(vm_name, name, description))
            self.active_tasks[name] = task
            
            # Clean up task when done
            task.add_done_callback(
                lambda t, n=name: self.active_tasks.pop(n, None)
            )
            
            return {
                "status": "started",
                "backup_name": name,
                "vm_name": vm_name,
                "start_time": datetime.utcnow().isoformat()
            }
        
        @self.router.get("/backups")
        async def list_backups() -> List[Dict[str, Any]]:
            """List all available backups."""
            backups = []
            for backup_dir in self.backup_dir.glob("*"):
                if not backup_dir.is_dir():
                    continue
                    
                # Get metadata
                metadata = self._read_metadata(backup_dir)
                if not metadata:
                    continue
                    
                backups.append({
                    "name": backup_dir.name,
                    "vm_name": metadata.get("vm_name", "unknown"),
                    "created_at": metadata.get("created_at", ""),
                    "description": metadata.get("description", ""),
                    "size": self._get_dir_size(backup_dir)
                })
            
            return sorted(backups, key=lambda x: x["created_at"], reverse=True)
        
        @self.router.delete("/backups/{backup_name}")
        async def delete_backup(backup_name: str) -> Dict[str, Any]:
            """Delete a backup."""
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists() or not backup_path.is_dir():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Backup '{backup_name}' not found"
                )
            
            try:
                shutil.rmtree(backup_path)
                return {"status": "deleted", "backup_name": backup_name}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete backup: {str(e)}"
                )
    
    async def _create_backup(
        self, 
        vm_name: str, 
        backup_name: str, 
        description: str = ""
    ) -> Dict[str, Any]:
        """Internal method to create a backup."""
        backup_path = self.backup_dir / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            metadata = {
                "vm_name": vm_name,
                "backup_name": backup_name,
                "created_at": datetime.utcnow().isoformat(),
                "description": description,
                "status": "in_progress"
            }
            self._write_metadata(backup_path, metadata)
            
            # In a real implementation, we would:
            # 1. Create a snapshot of the VM
            # 2. Export the VM to the backup directory
            # 3. Clean up the snapshot
            
            # Simulate backup process
            logger.info(f"Starting backup of VM '{vm_name}' to '{backup_name}'")
            await asyncio.sleep(5)  # Simulate backup time
            
            # Update metadata
            metadata.update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "size": self._get_dir_size(backup_path)
            })
            self._write_metadata(backup_path, metadata)
            
            logger.info(f"Backup completed: {backup_name}")
            return metadata
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Update metadata with error
            metadata.update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
            self._write_metadata(backup_path, metadata)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
    
    def _write_metadata(self, backup_path: Path, metadata: Dict[str, Any]) -> None:
        """Write metadata to backup directory."""
        import json
        with open(backup_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _read_metadata(self, backup_path: Path) -> Dict[str, Any]:
        """Read metadata from backup directory."""
        import json
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            return {}
            
        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata from {metadata_file}: {str(e)}")
            return {}
    
    def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of a directory in bytes."""
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
    
    async def cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy."""
        try:
            backups = []
            for backup_dir in self.backup_dir.glob("*"):
                if not backup_dir.is_dir():
                    continue
                    
                metadata = self._read_metadata(backup_dir)
                if not metadata or "created_at" not in metadata:
                    continue
                    
                try:
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    backups.append((backup_dir, created_at))
                except (ValueError, TypeError):
                    continue
            
            # Sort by creation date (oldest first)
            backups.sort(key=lambda x: x[1])
            
            # Remove old backups
            now = datetime.utcnow()
            removed = 0
            
            for backup_dir, created_at in backups:
                # Check if we've reached the max backups limit
                if len(backups) - removed <= self.max_backups:
                    break
                    
                # Check if backup is older than retention period
                age = (now - created_at).days
                if age >= self.retention_days:
                    try:
                        shutil.rmtree(backup_dir)
                        logger.info(f"Removed old backup: {backup_dir.name}")
                        removed += 1
                    except Exception as e:
                        logger.error(f"Failed to remove backup {backup_dir.name}: {str(e)}")
            
            return {"status": "completed", "removed": removed}
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}", exc_info=True)
            raise
    
    async def startup(self) -> None:
        """Start background tasks."""
        await super().startup()
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        await super().shutdown()
        
        # Cancel cleanup task
        if hasattr(self, 'cleanup_task'):
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up old backups."""
        while True:
            try:
                await self.cleanup_old_backups()
                # Run cleanup once per day
                await asyncio.sleep(24 * 60 * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}", exc_info=True)
                # Wait longer on error
                await asyncio.sleep(60 * 60)  # 1 hour
