"""
Storage Management Tools

This module contains tools for managing virtual storage devices and controllers.
"""

import asyncio
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Storage Controller Management


async def list_storage_controllers(vm_name: str) -> dict[str, Any]:
    """
    List all storage controllers for a virtual machine.

    Args:
        vm_name: Name or UUID of the VM

    Returns:
        Dictionary containing the list of storage controllers
    """
    try:
        cmd = ["VBoxManage", "showvminfo", vm_name, "--machinereadable"]
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        controllers = []
        current_controller = {}

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip('"')

                if key.startswith("storagecontrollername"):
                    if current_controller:
                        controllers.append(current_controller)
                    current_controller = {"name": value}
                elif key.startswith("storagecontrollertype"):
                    current_controller["type"] = value
                elif key.startswith("storagecontrollermaxportcount"):
                    current_controller["max_ports"] = int(value)
                elif key.startswith("storagecontrollerportcount"):
                    current_controller["port_count"] = int(value)
                elif key.startswith("storagecontrollerbootable"):
                    current_controller["bootable"] = value == "on"

        if current_controller:
            controllers.append(current_controller)

        return {"status": "success", "controllers": controllers}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing storage controllers for VM {vm_name}: {e}")
        return {"status": "error", "message": f"Failed to list storage controllers: {e.stderr}"}


async def create_storage_controller(
    vm_name: str,
    controller_name: str,
    controller_type: str,
    port_count: int = 2,
    bootable: bool = True,
) -> dict[str, Any]:
    """
    Create a new storage controller for a virtual machine.

    Args:
        vm_name: Name or UUID of the VM
        controller_name: Name for the new controller
        controller_type: Type of controller (e.g., 'SATA', 'SCSI', 'IDE', 'SAS')
        port_count: Number of ports (default: 2)
        bootable: Whether the controller is bootable

    Returns:
        Dictionary with controller creation status
    """
    try:
        # Add the storage controller
        cmd = [
            "VBoxManage",
            "storagectl",
            vm_name,
            "--name",
            controller_name,
            "--add",
            controller_type.lower(),
            "--portcount",
            str(port_count),
            "--bootable",
            "on" if bootable else "off",
        ]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        return {
            "status": "success",
            "message": f"Storage controller '{controller_name}' created successfully",
            "controller": {
                "name": controller_name,
                "type": controller_type,
                "port_count": port_count,
                "bootable": bootable,
            },
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating storage controller: {e}")
        return {"status": "error", "message": f"Failed to create storage controller: {e.stderr}"}


async def remove_storage_controller(vm_name: str, controller_name: str) -> dict[str, Any]:
    """
    Remove a storage controller from a virtual machine.

    Args:
        vm_name: Name or UUID of the VM
        controller_name: Name of the controller to remove

    Returns:
        Dictionary with controller removal status
    """
    try:
        cmd = ["VBoxManage", "storagectl", vm_name, "--name", controller_name, "--remove"]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        return {
            "status": "success",
            "message": f"Storage controller '{controller_name}' removed successfully",
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error removing storage controller: {e}")
        return {"status": "error", "message": f"Failed to remove storage controller: {e.stderr}"}


# Disk Management


async def attach_disk(
    vm_name: str,
    controller_name: str,
    port: int,
    device: int = 0,
    disk_type: str = "hdd",
    medium: str = "none",
    disk_format: str = "normal",
) -> dict[str, Any]:
    """
    Attach a disk to a virtual machine.

    Args:
        vm_name: Name or UUID of the VM
        controller_name: Name of the storage controller
        port: Port number on the controller
        device: Device number (0 for single disk)
        disk_type: Type of disk (hdd or dvddrive)
        medium: Path to the disk image or 'none' to remove disk
        disk_format: Type of disk controller (normal, writethrough, immutable, etc.)

    Returns:
        Dictionary with disk attachment status
    """
    try:
        cmd = [
            "VBoxManage",
            "storageattach",
            vm_name,
            "--storagectl",
            controller_name,
            "--port",
            str(port),
            "--device",
            str(device),
            "--type",
            disk_type,
            "--medium",
            medium,
            "--mtype",
            disk_format,
        ]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        action = "attached" if medium.lower() != "none" else "detached"
        return {
            "status": "success",
            "message": f"Disk {action} successfully",
            "details": {
                "controller": controller_name,
                "port": port,
                "device": device,
                "medium": medium if medium.lower() != "none" else None,
            },
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error attaching disk: {e}")
        return {"status": "error", "message": f"Failed to attach disk: {e.stderr}"}


async def detach_disk(
    vm_name: str, controller_name: str, port: int, device: int = 0
) -> dict[str, Any]:
    """
    Detach a disk from a virtual machine.

    Args:
        vm_name: Name or UUID of the VM
        controller_name: Name of the storage controller
        port: Port number on the controller
        device: Device number (0 for single disk)

    Returns:
        Dictionary with disk detachment status
    """
    return await attach_disk(
        vm_name=vm_name, controller_name=controller_name, port=port, device=device, medium="none"
    )


async def mount_iso(
    vm_name: str,
    iso_path: str,
    controller_name: str = "IDE Controller",
    port: int = 1,
    device: int = 0,
    temp: bool = False,
) -> dict[str, Any]:
    """
    Mount an ISO file to a VM's virtual optical drive.

    Args:
        vm_name: Name or UUID of the VM
        iso_path: Path to the ISO file (must be accessible from host)
        controller_name: Name of the storage controller (default: "IDE Controller")
        port: Port number on the controller (default: 1)
        device: Device number on the port (default: 0)
        temp: If True, the ISO will be mounted only until the next VM reboot (default: False)

    Returns:
        Dictionary with operation status and details
    """
    try:
        # First, check if there's already a disk in the specified location
        check_cmd = ["VBoxManage", "showvminfo", vm_name, "--machinereadable"]

        result = await asyncio.to_thread(
            subprocess.run, check_cmd, capture_output=True, text=True, check=True
        )

        # Check if there's already a disk at the specified location
        target_key = f"ide-{port}-{device}"
        has_existing = False

        for line in result.stdout.splitlines():
            if line.startswith(f'"{target_key}"='):
                has_existing = True
                break

        # If there's an existing disk and temp is False, unmount it first
        if has_existing and not temp:
            await unmount_iso(vm_name, controller_name, port, device)

        # Mount the ISO
        mount_cmd = [
            "VBoxManage",
            "storageattach",
            vm_name,
            "--storagectl",
            controller_name,
            "--port",
            str(port),
            "--device",
            str(device),
            "--type",
            "dvddrive",
            "--medium",
            iso_path,
        ]

        if temp:
            mount_cmd.append("--tempeject")

        await asyncio.to_thread(
            subprocess.run, mount_cmd, capture_output=True, text=True, check=True
        )

        return {
            "status": "success",
            "message": f"ISO mounted successfully to {controller_name}:{port},{device}",
            "details": {
                "iso_path": iso_path,
                "controller": controller_name,
                "port": port,
                "device": device,
                "temporary": temp,
            },
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error mounting ISO: {e}")
        return {"status": "error", "message": f"Failed to mount ISO: {e.stderr}"}


async def unmount_iso(
    vm_name: str, controller_name: str = "IDE Controller", port: int = 1, device: int = 0
) -> dict[str, Any]:
    """
    Unmount an ISO from a VM's optical drive.

    Args:
        vm_name: Name or UUID of the VM
        controller_name: Name of the storage controller
        port: Port number on the controller
        device: Device number on the port

    Returns:
        Dictionary containing unmount status
    """
    try:
        cmd = [
            "VBoxManage",
            "storageattach",
            vm_name,
            "--storagectl",
            controller_name,
            "--port",
            str(port),
            "--device",
            str(device),
            "--type",
            "dvddrive",
            "--medium",
            "none",
        ]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        return {
            "status": "success",
            "message": f"ISO unmounted from {controller_name}:{port},{device}",
            "details": {"controller": controller_name, "port": port, "device": device},
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error unmounting ISO: {e}")
        return {"status": "error", "message": f"Failed to unmount ISO: {e.stderr}"}


async def list_disks(vm_name: str) -> dict[str, Any]:
    """
    List all disks attached to a virtual machine.

    Args:
        vm_name: Name or UUID of the VM

    Returns:
        Dictionary containing the list of disks with their details
    """
    try:
        # Get VM storage controllers first
        controllers = await list_storage_controllers(vm_name)
        if controllers["status"] != "success":
            return controllers

        disks = []

        # For each controller, get attached disks
        for controller in controllers["controllers"]:
            controller_name = controller["name"]

            # Get storage controller details
            cmd = ["VBoxManage", "showvminfo", vm_name, "--machinereadable"]
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, check=True
            )

            # Parse the output to find attached disks
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip('"')
                value = value.strip('"')

                # Look for disk attachments
                if key.startswith(f"{controller_name.lower()}-") and "-ImageUUID-" in key:
                    # Extract port and device from the key
                    parts = key.split("-")
                    port = int(parts[1])
                    device = int(parts[3])

                    # Get disk info
                    disk_info = await get_disk_info(value)

                    if disk_info["status"] == "success":
                        disk = disk_info["disk_info"]
                        disk.update({"controller": controller_name, "port": port, "device": device})
                        disks.append(disk)

        return {"status": "success", "disks": disks}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing disks: {e}")
        return {"status": "error", "message": f"Failed to list disks: {e.stderr}"}


async def create_disk(
    disk_path: str, size_mb: int, disk_format: str = "VDI", variant: str = "Standard"
) -> dict[str, Any]:
    """
    Create a new virtual disk.

    Args:
        disk_path: Path to the new disk file
        size_mb: Size of the disk in MB
        disk_format: Disk format (VDI, VMDK, VHD, RAW)
        variant: Disk variant (Standard, Fixed, Split2G, Stream, ESX)

    Returns:
        Dictionary with disk creation status
    """
    try:
        # Validate disk format
        valid_formats = ["VDI", "VMDK", "VHD", "RAW"]
        if disk_format.upper() not in valid_formats:
            return {
                "status": "error",
                "message": f"Invalid disk format. Must be one of: {', '.join(valid_formats)}",
            }

        # Validate variant
        valid_variants = ["Standard", "Fixed", "Split2G", "Stream", "ESX"]
        if variant not in valid_variants:
            return {
                "status": "error",
                "message": f"Invalid variant. Must be one of: {', '.join(valid_variants)}",
            }

        # Create the disk
        cmd = [
            "VBoxManage",
            "createmedium",
            "disk",
            "--filename",
            disk_path,
            "--size",
            str(size_mb),
            "--format",
            disk_format.upper(),
            "--variant",
            variant,
        ]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        # Parse the output to get the UUID
        disk_uuid = None
        for line in result.stdout.splitlines():
            if "UUID:" in line:
                disk_uuid = line.split(":")[1].strip()
                break

        return {
            "status": "success",
            "message": f"Disk created successfully at {disk_path}",
            "disk_info": {
                "path": disk_path,
                "size_mb": size_mb,
                "format": disk_format.upper(),
                "variant": variant,
                "uuid": disk_uuid,
            },
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating disk: {e}")
        return {"status": "error", "message": f"Failed to create disk: {e.stderr}"}


async def get_disk_info(disk_identifier: str) -> dict[str, Any]:
    """
    Get information about a virtual disk.

    Args:
        disk_identifier: Path to the disk file or disk UUID

    Returns:
        Dictionary containing disk information
    """
    try:
        cmd = ["VBoxManage", "showmediuminfo", disk_identifier]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        disk_info = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Skip empty values
            if not value or value == "not available":
                continue

            # Convert known numeric values
            if key in ["Logical size", "Current size on disk"] and "bytes" in value:
                try:
                    value = int(value.split()[0])
                except (ValueError, IndexError):
                    pass

            disk_info[key] = value

        return {"status": "success", "disk_info": disk_info}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting disk info: {e}")
        return {"status": "error", "message": f"Failed to get disk info: {e.stderr}"}


async def resize_disk(disk_identifier: str, new_size_mb: int) -> dict[str, Any]:
    """
    Resize a virtual disk.

    Args:
        disk_identifier: Path to the disk file or disk UUID
        new_size_mb: New size of the disk in MB

    Returns:
        Dictionary with disk resize status
    """
    try:
        # First, get current disk info to check if resizing is possible
        disk_info = await get_disk_info(disk_identifier)
        if disk_info["status"] != "success":
            return disk_info

        # Check if the disk is in use
        if disk_info["disk_info"].get("State") == "locked":
            return {"status": "error", "message": "Cannot resize a disk that is in use"}

        # Resize the disk
        cmd = ["VBoxManage", "modifymedium", "disk", disk_identifier, "--resize", str(new_size_mb)]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        # Get updated disk info
        updated_info = await get_disk_info(disk_identifier)

        return {
            "status": "success",
            "message": f"Disk resized to {new_size_mb}MB",
            "disk_info": updated_info["disk_info"] if updated_info["status"] == "success" else None,
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error resizing disk: {e}")
        return {"status": "error", "message": f"Failed to resize disk: {e.stderr}"}


async def clone_disk(
    source_disk: str, target_disk: str, disk_format: str = "", variant: str = ""
) -> dict[str, Any]:
    """
    Clone a virtual disk.

    Args:
        source_disk: Path to the source disk file or UUID
        target_disk: Path to the target disk file
        disk_format: Target disk format (VDI, VMDK, VHD, RAW). If empty, uses source format.
        variant: Target disk variant (Standard, Fixed, Split2G, Stream, ESX). If empty, uses source variant.

    Returns:
        Dictionary with disk clone status
    """
    try:
        # Get source disk info to determine format if not specified
        if not disk_format:
            source_info = await get_disk_info(source_disk)
            if source_info["status"] != "success":
                return source_info
            disk_format = source_info["disk_info"].get("Format")
            if not disk_format:
                return {"status": "error", "message": "Could not determine source disk format"}

        # Build the clone command
        cmd = [
            "VBoxManage",
            "clonemedium",
            "disk",
            source_disk,
            target_disk,
            "--format",
            disk_format.upper(),
        ]

        if variant:
            cmd.extend(["--variant", variant])

        # Execute the clone
        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        # Get info about the new disk
        new_disk_info = await get_disk_info(target_disk)

        return {
            "status": "success",
            "message": f"Disk cloned to {target_disk}",
            "disk_info": new_disk_info["disk_info"]
            if new_disk_info["status"] == "success"
            else None,
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning disk: {e}")
        return {"status": "error", "message": f"Failed to clone disk: {e.stderr}"}


async def delete_disk(disk_identifier: str, force: bool = False) -> dict[str, Any]:
    """
    Delete a virtual disk.

    Args:
        disk_identifier: Path to the disk file or disk UUID to delete
        force: Force deletion even if the disk is in use

    Returns:
        Dictionary with disk deletion status
    """
    try:
        # Get disk info first to check if it's in use
        disk_info = await get_disk_info(disk_identifier)
        if disk_info["status"] != "success":
            return disk_info

        # Check if the disk is in use
        if not force and disk_info["disk_info"].get("State") == "locked":
            return {
                "status": "error",
                "message": "Disk is in use. Use force=True to delete anyway.",
            }

        # Delete the disk
        cmd = ["VBoxManage", "closemedium", "disk", disk_identifier, "--delete"]

        await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

        return {"status": "success", "message": f"Disk {disk_identifier} deleted successfully"}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error deleting disk: {e}")
        return {"status": "error", "message": f"Failed to delete disk: {e.stderr}"}
