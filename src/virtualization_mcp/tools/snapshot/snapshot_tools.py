"""
Snapshot Management Tools

This module contains tools for managing VM snapshots.
"""

import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

async def create_snapshot(
    vm_name: str,
    snapshot_name: str,
    description: str = "",
    live: bool = False
) -> Dict[str, Any]:
    """
    Create a snapshot of a virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM
        snapshot_name: Name for the new snapshot
        description: Optional description of the snapshot
        live: Whether to create a live snapshot without pausing the VM
        
    Returns:
        Dictionary with snapshot creation status
    """
    try:
        cmd = ["VBoxManage", "snapshot", vm_name, "take", snapshot_name]
        
        if description:
            cmd.extend(["--description", description])
        
        if live:
            cmd.append("--live")
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract the snapshot UUID from the output
        snapshot_uuid = None
        for line in result.stdout.splitlines():
            if "Snapshot taken. UUID:" in line:
                parts = line.split("UUID:")
                if len(parts) > 1:
                    snapshot_uuid = parts[1].strip()
                break
        
        return {
            "status": "success",
            "message": f"Snapshot '{snapshot_name}' created successfully",
            "snapshot": {
                "name": snapshot_name,
                "uuid": snapshot_uuid,
                "description": description,
                "live": live
            }
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating snapshot: {e}")
        return {
            "status": "error",
            "message": f"Failed to create snapshot: {e.stderr}"
        }

async def restore_snapshot(
    vm_name: str,
    snapshot_name: str,
    start_vm: bool = False
) -> Dict[str, Any]:
    """
    Restore a virtual machine to a previous snapshot.
    
    Args:
        vm_name: Name or UUID of the VM
        snapshot_name: Name or UUID of the snapshot to restore
        start_vm: Whether to start the VM after restoring the snapshot
        
    Returns:
        Dictionary with snapshot restore status
    """
    try:
        cmd = ["VBoxManage", "snapshot", vm_name, "restore", snapshot_name]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Start the VM if requested
        if start_vm:
            from ..vm.vm_tools import start_vm
            start_result = await start_vm(vm_name)
            
            if start_result["status"] != "success":
                return {
                    "status": "partial",
                    "message": f"Snapshot restored but failed to start VM: {start_result.get('message', 'Unknown error')}",
                    "snapshot_restored": True,
                    "vm_started": False
                }
            
            return {
                "status": "success",
                "message": f"Snapshot '{snapshot_name}' restored and VM started successfully",
                "snapshot_restored": True,
                "vm_started": True
            }
        
        return {
            "status": "success",
            "message": f"Snapshot '{snapshot_name}' restored successfully",
            "snapshot_restored": True,
            "vm_started": False
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error restoring snapshot: {e}")
        return {
            "status": "error",
            "message": f"Failed to restore snapshot: {e.stderr}",
            "snapshot_restored": False,
            "vm_started": False
        }

async def list_snapshots(vm_name: str) -> Dict[str, Any]:
    """
    List all snapshots for a virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM
        
    Returns:
        Dictionary containing the list of snapshots
    """
    try:
        cmd = ["VBoxManage", "snapshot", vm_name, "list", "--machinereadable"]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        snapshots = []
        current_snapshot = {}
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_snapshot:
                    snapshots.append(current_snapshot)
                    current_snapshot = {}
                continue
                
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip('"')
                
                if key == "SnapshotName":
                    if current_snapshot:  # Save previous snapshot if exists
                        snapshots.append(current_snapshot)
                    current_snapshot = {"name": value}
                elif key == "SnapshotUUID":
                    current_snapshot["uuid"] = value
                elif key == "Description":
                    current_snapshot["description"] = value
                elif key == "TimeStamp":
                    current_snapshot["timestamp"] = value
        
        if current_snapshot:  # Add the last snapshot
            snapshots.append(current_snapshot)
        
        return {
            "status": "success",
            "vm_name": vm_name,
            "snapshots": snapshots
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing snapshots: {e}")
        return {
            "status": "error",
            "message": f"Failed to list snapshots: {e.stderr}"
        }

async def get_snapshot_info(
    vm_name: str,
    snapshot_name: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific snapshot.
    
    Args:
        vm_name: Name or UUID of the VM
        snapshot_name: Name or UUID of the snapshot
        
    Returns:
        Dictionary containing snapshot information
    """
    try:
        # First, list all snapshots to find the one we're interested in
        snapshots = await list_snapshots(vm_name)
        if snapshots["status"] != "success":
            return snapshots
        
        # Find the snapshot by name or UUID
        target_snapshot = None
        for snapshot in snapshots.get("snapshots", []):
            if snapshot.get("name") == snapshot_name or snapshot.get("uuid") == snapshot_name:
                target_snapshot = snapshot
                break
        
        if not target_snapshot:
            return {
                "status": "error",
                "message": f"Snapshot '{snapshot_name}' not found"
            }
        
        # Get detailed information about the snapshot
        cmd = ["VBoxManage", "snapshot", vm_name, "showvminfo", target_snapshot["uuid"]]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the detailed information
        details = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
                
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Skip empty values
            if not value or value == 'not available':
                continue
                
            details[key] = value
        
        # Add the basic snapshot info
        details.update(target_snapshot)
        
        return {
            "status": "success",
            "snapshot_info": details
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting snapshot info: {e}")
        return {
            "status": "error",
            "message": f"Failed to get snapshot info: {e.stderr}"
        }

async def delete_snapshot(
    vm_name: str,
    snapshot_name: str
) -> Dict[str, Any]:
    """
    Delete a snapshot from a virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM
        snapshot_name: Name or UUID of the snapshot to delete
        
    Returns:
        Dictionary with snapshot deletion status
    """
    try:
        cmd = ["VBoxManage", "snapshot", vm_name, "delete", snapshot_name]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"Snapshot '{snapshot_name}' deleted successfully"
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error deleting snapshot: {e}")
        return {
            "status": "error",
            "message": f"Failed to delete snapshot: {e.stderr}"
        }

async def restore_current_snapshot(
    vm_name: str,
    start_vm: bool = False
) -> Dict[str, Any]:
    """
    Restore the current snapshot of a virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM
        start_vm: Whether to start the VM after restoring
        
    Returns:
        Dictionary with restore status
    """
    try:
        cmd = ["VBoxManage", "snapshot", vm_name, "restorecurrent"]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Start the VM if requested
        if start_vm:
            from ..vm.vm_tools import start_vm
            start_result = await start_vm(vm_name)
            
            if start_result["status"] != "success":
                return {
                    "status": "partial",
                    "message": f"Current snapshot restored but failed to start VM: {start_result.get('message', 'Unknown error')}",
                    "snapshot_restored": True,
                    "vm_started": False
                }
            
            return {
                "status": "success",
                "message": "Current snapshot restored and VM started successfully",
                "snapshot_restored": True,
                "vm_started": True
            }
        
        return {
            "status": "success",
            "message": "Current snapshot restored successfully",
            "snapshot_restored": True,
            "vm_started": False
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error restoring current snapshot: {e}")
        return {
            "status": "error",
            "message": f"Failed to restore current snapshot: {e.stderr}",
            "snapshot_restored": False,
            "vm_started": False
        }
