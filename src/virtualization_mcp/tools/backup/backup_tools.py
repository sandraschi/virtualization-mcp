"""
Backup Tools for VirtualBox VM Management

This module provides functionality for creating, listing, and managing backups
of VirtualBox virtual machines. Combines features from both backup implementations.
"""

import os
import shutil
import json
import logging
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

from virtualization_mcp.utils.helpers import get_vbox_home, ensure_dir_exists

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR_NAME = "backups"
BACKUP_CONFIG_FILE = "backup_config.json"


def get_backup_dir() -> Path:
    """Get the backup directory path.
    
    Returns:
        Path: Path to the backup directory.
    """
    # Use user's app data directory instead of VirtualBox program directory
    import os
    from pathlib import Path
    
    # Try to use LOCALAPPDATA first (Windows)
    if 'LOCALAPPDATA' in os.environ:
        app_data = Path(os.environ['LOCALAPPDATA'])
    # Fallback to HOME directory (Unix-like systems)
    elif 'HOME' in os.environ:
        app_data = Path(os.environ['HOME']) / '.local' / 'share'
    else:
        # Last resort: current directory
        app_data = Path.cwd()
    
    # Create virtualization-mcp subdirectory in the app data directory
    backup_dir = app_data / 'virtualization-mcp' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Set appropriate permissions (Unix-like systems)
    if hasattr(os, 'chmod'):
        try:
            os.chmod(backup_dir, 0o700)  # rwx------
        except Exception as e:
            logger.warning(f"Could not set permissions on backup directory: {e}")
    
    logger.info(f"Using backup directory: {backup_dir}")
    return backup_dir


def get_backup_config() -> Dict:
    """Load the backup configuration.
    
    Returns:
        Dict: Backup configuration.
    """
    backup_dir = get_backup_dir()
    config_file = backup_dir / BACKUP_CONFIG_FILE
    
    if not config_file.exists():
        return {"backups": {}, "next_id": 1}
        
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading backup config: {e}")
        return {"backups": {}, "next_id": 1}


def save_backup_config(config: Dict) -> bool:
    """Save the backup configuration.
    
    Args:
        config: Configuration to save.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    backup_dir = get_backup_dir()
    config_file = backup_dir / BACKUP_CONFIG_FILE
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except (TypeError, IOError) as e:
        logger.error(f"Error saving backup config: {e}")
        return False

def create_backup_legacy(vm_name: str, description: str = "") -> Dict:
    """Create a backup of a virtual machine.
    
    Args:
        vm_name: Name of the VM to backup.
        description: Optional description for the backup.
        
    Returns:
        Dict: Backup information or error details.
    """
    try:
        from vboxapi import VirtualBoxManager
        
        # Initialize VirtualBox
        mgr = VirtualBoxManager(None, None)
        vbox = mgr.getVirtualBox()
        
        # Get VM
        try:
            vm = vbox.findMachine(vm_name)
            if not vm:
                return {"status": "error", "message": f"VM '{vm_name}' not found"}
                
            # Create backup directory
            backup_dir = get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{vm_name}_{timestamp}"
            backup_path = backup_dir / backup_name
            
            # Save VM configuration
            vm_config = {
                "name": vm_name,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "backup_path": str(backup_path)
            }
            
            # Save VM state if running
            was_running = False
            session = mgr.mgr.getSessionObject(vbox)
            
            try:
                if vm.state == mgr.constants.MachineState_Running:
                    was_running = True
                    vm.saveSettings()
                    
                # Export the VM
                progress = mgr.mgr.exportMachines([vm.id], str(backup_path))
                progress.waitForCompletion(-1)
                
                if progress.resultCode != 0:
                    return {"status": "error", "message": f"Backup failed: {progress.errorInfo.text}"}
                
                # Update backup config
                config = get_backup_config()
                backup_id = str(config["next_id"])
                config["backups"][backup_id] = vm_config
                config["next_id"] += 1
                
                if not save_backup_config(config):
                    return {"status": "error", "message": "Failed to save backup configuration"}
                
                return {
                    "status": "success",
                    "backup_id": backup_id,
                    "backup_path": str(backup_path),
                    "vm_name": vm_name,
                    "timestamp": vm_config["timestamp"]
                }
                
            finally:
                if was_running and vm.state != mgr.constants.MachineState_Running:
                    vm.launchVMProcess(session, "headless", "")
                
                if session:
                    session.unlockMachine()
                    
        finally:
            if 'mgr' in locals():
                mgr.cleanup()
                
    except Exception as e:
        logger.exception("Error creating backup")
        return {"status": "error", "message": f"Failed to create backup: {str(e)}"}


def list_backups(vm_name: Optional[str] = None) -> List[Dict]:
    """List all backups, optionally filtered by VM name.
    
    Args:
        vm_name: Optional VM name to filter backups.
        
    Returns:
        List[Dict]: List of backup information dictionaries.
    """
    try:
        config = get_backup_config()
        backups = []
        
        for backup_id, backup in config["backups"].items():
            if vm_name and backup["name"] != vm_name:
                continue
                
            backup_info = {
                "backup_id": backup_id,
                "vm_name": backup["name"],
                "description": backup.get("description", ""),
                "timestamp": backup["timestamp"],
                "backup_path": backup["backup_path"]
            }
            backups.append(backup_info)
            
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
        
    except Exception as e:
        logger.exception("Error listing backups")
        return []


def delete_backup(backup_id: str) -> Dict:
    """Delete a backup by ID.
    
    Args:
        backup_id: ID of the backup to delete.
        
    Returns:
        Dict: Status of the operation.
    """
    try:
        config = get_backup_config()
        
        if backup_id not in config["backups"]:
            return {"status": "error", "message": f"Backup ID {backup_id} not found"}
            
        backup = config["backups"][backup_id]
        backup_path = Path(backup["backup_path"])
        
        # Remove backup directory
        if backup_path.exists():
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            else:
                backup_path.unlink()
                
        # Update config
        del config["backups"][backup_id]
        
        if not save_backup_config(config):
            return {"status": "error", "message": "Failed to update backup configuration"}
            
        return {
            "status": "success",
            "message": f"Backup {backup_id} deleted successfully"
        }
        
    except Exception as e:
        logger.exception(f"Error deleting backup {backup_id}")
        return {"status": "error", "message": f"Failed to delete backup: {str(e)}"}


class BackupManager:
    """
    A class to manage VM backups with a clean, object-oriented interface.
    
    This class provides methods to create, list, restore, and manage VM backups
    with additional features like retention policies and status monitoring.
    """
    
    def __init__(self):
        """Initialize the BackupManager with the current configuration."""
        self.config = get_backup_config()
        self.backup_dir = get_backup_dir()
    
    def create_backup(self, vm_name: str, description: str = "") -> Dict:
        """
        Create a backup of a virtual machine.
        
        Args:
            vm_name: Name of the VM to backup.
            description: Optional description for the backup.
            
        Returns:
            Dict: Backup information or error details.
        """
        return create_backup_legacy(vm_name, description)
    
    def list_backups(self, vm_name: Optional[str] = None) -> List[Dict]:
        """
        List all backups, optionally filtered by VM name.
        
        Args:
            vm_name: Optional VM name to filter backups.
            
        Returns:
            List[Dict]: List of backup information dictionaries.
        """
        return list_backups(vm_name)
    
    def get_backup(self, backup_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific backup.
        
        Args:
            backup_id: ID of the backup to retrieve.
            
        Returns:
            Optional[Dict]: Backup details if found, None otherwise.
        """
        self.config = get_backup_config()  # Refresh config
        backup = self.config.get("backups", {}).get(backup_id)
        if backup:
            return {"backup_id": backup_id, **backup}
        return None
    
    def delete_backup(self, backup_id: str) -> Dict:
        """
        Delete a backup by ID.
        
        Args:
            backup_id: ID of the backup to delete.
            
        Returns:
            Dict: Status of the operation.
        """
        return delete_backup(backup_id)
    
    def restore_backup(self, backup_id: str, vm_name: Optional[str] = None, overwrite: bool = False) -> Dict:
        """
        Restore a VM from a backup.
        
        Args:
            backup_id: ID of the backup to restore.
            vm_name: Optional new name for the restored VM.
            overwrite: If True, will overwrite an existing VM with the same name.
            
        Returns:
            Dict: Status of the restore operation.
        """
        try:
            from vboxapi import VirtualBoxManager
            
            # Get backup information
            backup = self.get_backup(backup_id)
            if not backup:
                return {"status": "error", "message": f"Backup with ID {backup_id} not found"}
                
            backup_path = Path(backup["backup_path"])
            if not backup_path.exists():
                return {"status": "error", "message": f"Backup files not found: {backup_path}"}
                
            target_name = vm_name or backup["vm_name"]
            
            # Initialize VirtualBox
            mgr = VirtualBoxManager(None, None)
            vbox = mgr.getVirtualBox()
            
            # Check if VM with target name already exists
            if vbox.findMachine(target_name) is not None:
                if not overwrite:
                    return {
                        "status": "error", 
                        "message": f"VM '{target_name}' already exists. Use overwrite=True to replace it."
                    }
                
            # Restore the VM
            progress = mgr.mgr.importAppliance(str(backup_path / f"{backup_id}.ovf"))
            progress.waitForCompletion(-1)
            
            if progress.resultCode != 0:
                return {"status": "error", "message": f"Restore failed: {progress.errorInfo.text}"}
            
            # Rename the VM if needed
            if vm_name and vm_name != backup["vm_name"]:
                vm = vbox.findMachine(backup["vm_name"])
                if vm:
                    session = mgr.mgr.getSessionObject(vbox)
                    vm.lockMachine(session, mgr.constants.LockType_Write)
                    machine = session.machine
                    machine.name = vm_name
                    machine.saveSettings()
                    session.unlockMachine()
            
            return {
                "status": "success",
                "message": f"Successfully restored VM '{target_name}' from backup {backup_id}",
                "backup_id": backup_id,
                "vm_name": target_name
            }
            
        except Exception as e:
            logger.exception(f"Error restoring backup {backup_id}")
            return {
                "status": "error",
                "message": f"Failed to restore backup: {str(e)}",
                "backup_id": backup_id
            }
        finally:
            if 'mgr' in locals():
                mgr.cleanup()
    
    def cleanup_old_backups(self, days_old: int = 30, max_backups: Optional[int] = None) -> Dict:
        """
        Clean up old backups based on age and/or maximum count.
        
        Args:
            days_old: Delete backups older than this many days.
            max_backups: Maximum number of backups to keep (oldest will be deleted first).
            
        Returns:
            Dict: Summary of the cleanup operation.
        """
        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=days_old)
            backups = self.list_backups()
            
            # Sort by timestamp (oldest first)
            backups_sorted = sorted(backups, key=lambda x: x.get("timestamp", ""))
            
            deleted = 0
            errors = []
            
            # Delete by age
            for backup in backups_sorted:
                backup_date = datetime.fromisoformat(backup["timestamp"].replace('Z', '+00:00'))
                if backup_date < cutoff_date:
                    result = self.delete_backup(backup["backup_id"])
                    if result.get("status") == "success":
                        deleted += 1
                    else:
                        errors.append(f"Failed to delete backup {backup['backup_id']}: {result.get('message')}")
            
            # Delete by count if needed
            if max_backups is not None:
                current_count = len(backups) - deleted
                if current_count > max_backups:
                    to_delete = current_count - max_backups
                    for backup in backups_sorted:
                        if to_delete <= 0:
                            break
                        if backup["backup_id"] not in [b["backup_id"] for b in backups_sorted[-max_backups:]]:
                            result = self.delete_backup(backup["backup_id"])
                            if result.get("status") == "success":
                                deleted += 1
                                to_delete -= 1
                            else:
                                errors.append(f"Failed to delete backup {backup['backup_id']}: {result.get('message')}")
            
            return {
                "status": "success",
                "deleted_count": deleted,
                "errors": errors
            }
            
        except Exception as e:
            logger.exception("Error during backup cleanup")
            return {
                "status": "error",
                "message": f"Backup cleanup failed: {str(e)}",
                "deleted_count": deleted,
                "errors": errors
            }


# Create a singleton instance for convenience
backup_manager = BackupManager()
