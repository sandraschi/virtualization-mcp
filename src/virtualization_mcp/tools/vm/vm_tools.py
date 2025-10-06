"""
Virtual Machine Management Tools

This module provides comprehensive tools for managing VirtualBox virtual machines
through the VirtualBox command-line interface (VBoxManage).
"""

import asyncio
import logging
import subprocess
import platform
import os
from typing import Dict, Any, Optional, List, Union, Literal

logger = logging.getLogger(__name__)

# Type aliases
VMState = Literal["poweroff", "running", "saved", "paused", "aborted"]
CloneMode = Literal["full", "linked", "all"]
VMStartType = Literal["gui", "sdl", "headless", "separate"]

async def list_vms(
    details: bool = False, 
    state_filter: Optional[VMState] = None
) -> Dict[str, Any]:
    """
    List all VirtualBox VMs with their current state.
    
    Args:
        details: If True, include detailed information about each VM
        state_filter: Optional filter to show only VMs in specific state
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - count: Number of VMs found
        - vms: List of VM information dictionaries
        - message: Error message if status is "error"
    """
    try:
        cmd = ["VBoxManage", "list", "vms", "--long"]
        if state_filter:
            cmd.extend(["--state", state_filter])
            
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        vms = []
        current_vm = {}
        
        # Parse VM information
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_vm:
                    vms.append(current_vm)
                    current_vm = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                current_vm[key] = value
        
        if current_vm:
            vms.append(current_vm)
            
        return {
            "status": "success",
            "count": len(vms),
            "vms": vms
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to list VMs: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "count": 0,
            "vms": []
        }
    except Exception as e:
        error_msg = f"Unexpected error listing VMs: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "count": 0,
            "vms": []
        }

async def get_vm_info(vm_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific VM.
    
    Args:
        vm_name: Name or UUID of the VM
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - vm_info: Dictionary of VM properties if successful
        - message: Error message if status is "error"
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string",
            "vm_info": None
        }
    
    try:
        cmd = ["VBoxManage", "showvminfo", vm_name, "--machinereadable"]
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        info = {}
        for line in result.stdout.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.strip()] = value.strip('"')
                
        return {
            "status": "success",
            "vm_info": info
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to get VM info for {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "vm_info": None
        }
    except Exception as e:
        error_msg = f"Unexpected error getting VM info: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "vm_info": None
        }

async def create_vm(
    name: str,
    ostype: str = "Ubuntu_64",
    memory_mb: int = 2048,
    cpu_count: int = 2,
    disk_size_gb: int = 20,
    net_type: str = "nat",
    start_after_create: bool = False
) -> Dict[str, Any]:
    """
    Create a new VirtualBox virtual machine.
    
    Args:
        name: Name for the new VM (must be unique)
        ostype: OS type (e.g., 'Ubuntu_64', 'Windows10_64')
        memory_mb: Memory allocation in MB (min 128, max depends on host)
        cpu_count: Number of virtual CPUs (1-32)
        disk_size_gb: Size of the primary disk in GB (min 1, max depends on storage)
        net_type: Network type (nat, bridged, intnet, hostonly, none)
        start_after_create: Whether to start the VM after creation
        
    Returns:
        Dictionary with creation status and VM details
    """
    # Input validation
    if not name or not isinstance(name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    if not isinstance(memory_mb, int) or memory_mb < 128:
        return {
            "status": "error",
            "message": "Memory must be at least 128MB"
        }
    
    if not isinstance(cpu_count, int) or cpu_count < 1 or cpu_count > 32:
        return {
            "status": "error",
            "message": "CPU count must be between 1 and 32"
        }
    
    if not isinstance(disk_size_gb, int) or disk_size_gb < 1:
        return {
            "status": "error",
            "message": "Disk size must be at least 1GB"
        }
    
    valid_net_types = ["nat", "bridged", "intnet", "hostonly", "none"]
    if net_type not in valid_net_types:
        return {
            "status": "error",
            "message": f"Invalid network type. Must be one of: {', '.join(valid_net_types)}"
        }
    
    try:
        # Create VM
        create_cmd = [
            "VBoxManage", "createvm",
            "--name", name,
            "--ostype", ostype,
            "--register"
        ]
        
        await asyncio.to_thread(
            subprocess.run,
            create_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Configure basic settings
        modify_cmds = [
            ["VBoxManage", "modifyvm", name, "--memory", str(memory_mb)],
            ["VBoxManage", "modifyvm", name, "--cpus", str(cpu_count)],
            ["VBoxManage", "modifyvm", name, "--graphicscontroller", "vmsvga"],
            ["VBoxManage", "modifyvm", name, "--vram", "128"]
        ]
        
        # Add network configuration if not 'none'
        if net_type != "none":
            modify_cmds.append(["VBoxManage", "modifyvm", name, "--nic1", net_type])
        
        for cmd in modify_cmds:
            await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        
        # Create and attach storage if disk size > 0
        disk_path = f"{name}_disk.vdi"
        if disk_size_gb > 0:
            create_disk_cmd = [
                "VBoxManage", "createhd",
                "--filename", disk_path,
                "--size", str(disk_size_gb * 1024),  # Convert GB to MB
                "--format", "VDI"
            ]
            
            await asyncio.to_thread(
                subprocess.run,
                create_disk_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Attach storage controller and disk
            storage_cmds = [
                ["VBoxManage", "storagectl", name, "--name", "SATA", "--add", "sata"],
                ["VBoxManage", "storageattach", name, "--storagectl", "SATA", 
                 "--port", "0", "--device", "0", "--type", "hdd", "--medium", disk_path]
            ]
            
            for cmd in storage_cmds:
                await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
        
        # Start VM if requested
        if start_after_create and disk_size_gb > 0:
            start_result = await start_vm(name)
            if start_result["status"] != "success":
                logger.warning(f"VM created but failed to start: {start_result['message']}")
        
        return {
            "status": "success",
            "message": f"VM '{name}' created successfully",
            "vm_name": name,
            "disk_path": disk_path if disk_size_gb > 0 else None
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error creating VM: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error creating VM: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

async def start_vm(
    vm_name: str, 
    start_type: VMStartType = "headless"
) -> Dict[str, Any]:
    """
    Start a virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM to start
        start_type: How to start the VM (gui, sdl, headless, separate)
        
    Returns:
        Dictionary with start operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    valid_types = ["gui", "sdl", "headless", "separate"]
    if start_type not in valid_types:
        return {
            "status": "error",
            "message": f"Invalid start type. Must be one of: {', '.join(valid_types)}"
        }
    
    try:
        cmd = ["VBoxManage", "startvm", vm_name, "--type", start_type]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{vm_name}' started successfully in {start_type} mode"
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to start VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error starting VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Export the public API
async def stop_vm(
    vm_name: str,
    force: bool = False,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Stop a running virtual machine gracefully or forcefully.
    
    Args:
        vm_name: Name or UUID of the VM to stop
        force: If True, force power off the VM (equivalent to pulling the plug)
        timeout: Time in seconds to wait for graceful shutdown before forcing (if force=True)
        
    Returns:
        Dictionary with stop operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    try:
        if force:
            # First try to gracefully shut down the VM
            try:
                cmd = ["VBoxManage", "controlvm", vm_name, "acpipowerbutton"]
                
                await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=timeout
                )
                
                return {
                    "status": "success",
                    "message": f"VM '{vm_name}' was gracefully shut down"
                }
                
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # If graceful shutdown fails or times out, force power off
                cmd = ["VBoxManage", "controlvm", vm_name, "poweroff"]
                
                await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                return {
                    "status": "success",
                    "message": f"VM '{vm_name}' was force stopped"
                }
                
        else:
            # Just send ACPI power button event
            cmd = ["VBoxManage", "controlvm", vm_name, "acpipowerbutton"]
            
            await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "status": "success",
                "message": f"ACPI power button event sent to VM '{vm_name}'. The guest OS may ignore this request."
            }
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to stop VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error stopping VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Export the public API
async def delete_vm(
    vm_name: str,
    delete_files: bool = True
) -> Dict[str, Any]:
    """
    Delete a virtual machine and optionally its associated files.
    
    Args:
        vm_name: Name or UUID of the VM to delete
        delete_files: If True, also delete all associated files (disks, logs, etc.)
        
    Returns:
        Dictionary with delete operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    try:
        # First try to stop the VM if it's running
        try:
            await stop_vm(vm_name, force=True)
        except Exception as e:
            logger.warning(f"Could not stop VM {vm_name} before deletion: {str(e)}")
        
        # Build the unregister command
        cmd = ["VBoxManage", "unregistervm", vm_name]
        
        if delete_files:
            cmd.append("--delete")
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{vm_name}' has been deleted" + (" with all associated files" if delete_files else " (files preserved)")
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to delete VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error deleting VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Export the public API
async def clone_vm(
    source_vm: str,
    new_name: str,
    snapshot: Optional[str] = None,
    mode: CloneMode = "full",
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a clone of an existing virtual machine.
    
    Args:
        source_vm: Name or UUID of the VM to clone
        new_name: Name for the new VM (must be unique)
        snapshot: Name of the snapshot to clone from (optional)
        mode: Clone mode - 'full' (default), 'linked', or 'all'
        options: Additional clone options as key-value pairs
            - register: bool - Register the clone in VirtualBox (default: True)
            - keepallmacs: bool - Keep all MAC addresses (default: False)
            - keepdisknames: bool - Keep disk names (default: False)
            - keephwuuids: bool - Keep hardware UUIDs (default: False)
            - keepnathmac: bool - Keep NAT MAC addresses (default: False)
            - keepallmacs: bool - Keep all MAC addresses (default: False)
            - keepdisknames: bool - Keep disk names (default: False)
            - keepallmacs: bool - Keep all MAC addresses (default: False)
    
    Returns:
        Dictionary with clone operation status
    """
    if not source_vm or not isinstance(source_vm, str):
        return {
            "status": "error",
            "message": "Source VM name must be a non-empty string"
        }
        
    if not new_name or not isinstance(new_name, str):
        return {
            "status": "error",
            "message": "New VM name must be a non-empty string"
        }
    
    if mode not in ["full", "linked", "all"]:
        return {
            "status": "error",
            "message": "Invalid clone mode. Must be 'full', 'linked', or 'all'"
        }
    
    try:
        cmd = ["VBoxManage", "clonevm", source_vm, "--name", new_name, "--register"]
        
        if snapshot:
            cmd.extend(["--snapshot", snapshot])
            
        if mode == "linked":
            cmd.append("--options=link")
        elif mode == "all":
            cmd.append("--options=all")
        
        # Add additional options
        if options:
            for key, value in options.items():
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key}")
                elif value is not None:
                    cmd.extend([f"--{key}", str(value)])
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{source_vm}' cloned to '{new_name}' successfully",
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error cloning VM {source_vm} to {new_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": f"Failed to clone VM: {error_msg}"
        }
    except Exception as e:
        error_msg = f"Unexpected error cloning VM {source_vm}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Export the public API
async def modify_vm(
    vm_name: str,
    memory_mb: Optional[int] = None,
    cpu_count: Optional[int] = None,
    vram_mb: Optional[int] = None,
    description: Optional[str] = None,
    ostype: Optional[str] = None,
    nic1: Optional[str] = None,
    nictype1: Optional[str] = None,
    nic2: Optional[str] = None,
    nictype2: Optional[str] = None,
    nic3: Optional[str] = None,
    nictype3: Optional[str] = None,
    nic4: Optional[str] = None,
    nictype4: Optional[str] = None,
    audio: Optional[bool] = None,
    clipboard: Optional[str] = None,
    draganddrop: Optional[str] = None,
    vrde: Optional[bool] = None,
    vrde_port: Optional[int] = None,
    vrde_address: Optional[str] = None,
    vrde_auth_type: Optional[str] = None,
    vrde_auth_library: Optional[str] = None,
    vrde_property: Optional[Dict[str, str]] = None,
    **extra_params
) -> Dict[str, Any]:
    """
    Modify VM settings.
    
    Args:
        vm_name: Name or UUID of the VM to modify
        memory_mb: New memory allocation in MB
        cpu_count: Number of virtual CPUs
        vram_mb: Video memory in MB
        description: New description for the VM
        ostype: Change the OS type (use 'VBoxManage list ostypes' to see available types)
        nic1-4: Network interface configuration (nat, bridged, intnet, hostonly, none)
        nictype1-4: Network adapter type (e.g., 82540EM, virtio, etc.)
        audio: Enable/disable audio (True/False)
        clipboard: Clipboard mode (disabled, hosttoguest, guesttohost, bidirectional)
        draganddrop: Drag and drop mode (disabled, hosttoguest, guesttohost, bidirectional)
        vrde: Enable/disable VRDE server (True/False)
        vrde_port: VRDE server port
        vrde_address: VRDE server address
        vrde_auth_type: VRDE authentication type (null, external, guest, external+guest)
        vrde_auth_library: VRDE authentication library
        vrde_property: Dictionary of VRDE properties (key=value)
        extra_params: Additional parameters to pass to modifyvm
        
    Returns:
        Dictionary with modification status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    changes = []
    
    try:
        # Build the base command
        cmd = ["VBoxManage", "modifyvm", vm_name]
        
        # Handle memory
        if memory_mb is not None:
            if not isinstance(memory_mb, int) or memory_mb < 4:
                return {
                    "status": "error",
                    "message": "Memory must be at least 4MB"
                }
            cmd.extend(["--memory", str(memory_mb)])
            changes.append(f"memory={memory_mb}MB")
        
        # Handle CPU count
        if cpu_count is not None:
            if not isinstance(cpu_count, int) or cpu_count < 1 or cpu_count > 32:
                return {
                    "status": "error",
                    "message": "CPU count must be between 1 and 32"
                }
            cmd.extend(["--cpus", str(cpu_count)])
            changes.append(f"cpus={cpu_count}")
        
        # Handle VRAM
        if vram_mb is not None:
            if not isinstance(vram_mb, int) or vram_mb < 1 or vram_mb > 256:
                return {
                    "status": "error",
                    "message": "VRAM must be between 1MB and 256MB"
                }
            cmd.extend(["--vram", str(vram_mb)])
            changes.append(f"vram={vram_mb}MB")
        
        # Handle description
        if description is not None:
            cmd.extend(["--description", f'"{description}"'])
            changes.append("description updated")
        
        # Handle OS type
        if ostype is not None:
            cmd.extend(["--ostype", ostype])
            changes.append(f"ostype={ostype}")
        
        # Handle network interfaces
        for i in range(1, 5):
            nic = locals().get(f'nic{i}')
            nictype = locals().get(f'nictype{i}')
            
            if nic is not None:
                valid_nic_modes = ["none", "null", "nat", "bridged", "intnet", "hostonly", "generic"]
                if nic.lower() not in valid_nic_modes:
                    return {
                        "status": "error",
                        "message": f"Invalid NIC{i} mode. Must be one of: {', '.join(valid_nic_modes)}"
                    }
                
                cmd.extend([f"--nic{i}", nic])
                changes.append(f"nic{i}={nic}")
                
                if nictype is not None:
                    valid_nic_types = ["Am79C970A", "Am79C973", "82540EM", "82543GC", "82545EM", "virtio"]
                    if nictype not in valid_nic_types:
                        return {
                            "status": "error",
                            "message": f"Invalid NIC{i} type. Must be one of: {', '.join(valid_nic_types)}"
                        }
                    cmd.extend([f"--nictype{i}", nictype])
                    changes.append(f"nictype{i}={nictype}")
        
        # Handle audio
        if audio is not None:
            cmd.append("--audio" if audio else "--audio none")
            changes.append(f"audio={'on' if audio else 'off'}")
        
        # Handle clipboard
        if clipboard is not None:
            valid_clipboard_modes = ["disabled", "hosttoguest", "guesttohost", "bidirectional"]
            if clipboard not in valid_clipboard_modes:
                return {
                    "status": "error",
                    "message": f"Invalid clipboard mode. Must be one of: {', '.join(valid_clipboard_modes)}"
                }
            cmd.extend(["--clipboard", clipboard])
            changes.append(f"clipboard={clipboard}")
        
        # Handle drag and drop
        if draganddrop is not None:
            valid_dnd_modes = ["disabled", "hosttoguest", "guesttohost", "bidirectional"]
            if draganddrop not in valid_dnd_modes:
                return {
                    "status": "error",
                    "message": f"Invalid drag and drop mode. Must be one of: {', '.join(valid_dnd_modes)}"
                }
            cmd.extend(["--draganddrop", draganddrop])
            changes.append(f"draganddrop={draganddrop}")
        
        # Handle VRDE settings
        if vrde is not None:
            if vrde:
                cmd.append("--vrde")
                changes.append("vrde=on")
            else:
                cmd.append("--vrde off")
                changes.append("vrde=off")
        
        if vrde_port is not None:
            cmd.extend(["--vrdeport", str(vrde_port)])
            changes.append(f"vrde_port={vrde_port}")
        
        if vrde_address is not None:
            cmd.extend(["--vrdeaddress", vrde_address])
            changes.append(f"vrde_address={vrde_address}")
        
        if vrde_auth_type is not None:
            valid_auth_types = ["null", "external", "guest", "external+guest"]
            if vrde_auth_type not in valid_auth_types:
                return {
                    "status": "error",
                    "message": f"Invalid VRDE auth type. Must be one of: {', '.join(valid_auth_types)}"
                }
            cmd.extend(["--vrdemulticon", vrde_auth_type])
            changes.append(f"vrde_auth_type={vrde_auth_type}")
        
        if vrde_auth_library is not None:
            cmd.extend(["--vrdeauthlibrary", vrde_auth_library])
            changes.append(f"vrde_auth_library={vrde_auth_library}")
        
        if vrde_property is not None:
            for key, value in vrde_property.items():
                cmd.extend(["--vrdeproperty", f"{key}={value}"])
                changes.append(f"vrde_property_{key}={value}")
        
        # Handle extra parameters
        for key, value in extra_params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            elif value is not None:
                cmd.extend([f"--{key}", str(value)])
        
        # Only run the command if there are changes to make
        if len(cmd) > 3:  # More than just ["VBoxManage", "modifyvm", vm_name]
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "status": "success",
                "message": f"VM '{vm_name}' modified successfully",
                "changes": changes,
                "output": result.stdout
            }
        else:
            return {
                "status": "success",
                "message": "No changes were made to the VM configuration",
                "changes": []
            }
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to modify VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "changes": changes
        }
    except Exception as e:
        error_msg = f"Unexpected error modifying VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "changes": changes
        }

# Export the public API
async def pause_vm(vm_name: str) -> Dict[str, Any]:
    """
    Pause a running virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM to pause
    
    Returns:
        Dictionary with pause operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    try:
        cmd = ["VBoxManage", "controlvm", vm_name, "pause"]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{vm_name}' has been paused"
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to pause VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error pausing VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }


async def resume_vm(vm_name: str) -> Dict[str, Any]:
    """
    Resume a paused virtual machine.
    
    Args:
        vm_name: Name or UUID of the VM to resume
    
    Returns:
        Dictionary with resume operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    try:
        cmd = ["VBoxManage", "controlvm", vm_name, "resume"]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{vm_name}' has been resumed"
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to resume VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error resuming VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }


async def reset_vm(
    vm_name: str,
    reset_type: str = "hard"
) -> Dict[str, Any]:
    """
    Reset a virtual machine (hard reset).
    
    Args:
        vm_name: Name or UUID of the VM to reset
        reset_type: Type of reset to perform ('hard' or 'soft')
            - 'hard': Power cycle the VM (equivalent to pressing the reset button)
            - 'soft': Send ACPI reset signal (requires guest additions)
    
    Returns:
        Dictionary with reset operation status
    """
    if not vm_name or not isinstance(vm_name, str):
        return {
            "status": "error",
            "message": "VM name must be a non-empty string"
        }
    
    if reset_type not in ["hard", "soft"]:
        return {
            "status": "error",
            "message": "Invalid reset type. Must be 'hard' or 'soft'"
        }
    
    try:
        if reset_type == "hard":
            cmd = ["VBoxManage", "controlvm", vm_name, "reset"]
        else:
            cmd = ["VBoxManage", "controlvm", vm_name, "acpisleepbutton"]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"VM '{vm_name}' has been {reset_type} reset"
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to reset VM {vm_name}: {e.stderr.strip()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error resetting VM {vm_name}: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Export the public API
__all__ = [
    'list_vms',
    'get_vm_info',
    'create_vm',
    'start_vm',
    'stop_vm',
    'delete_vm',
    'clone_vm',
    'modify_vm',
    'reset_vm',
    'pause_vm',
    'resume_vm'
]
