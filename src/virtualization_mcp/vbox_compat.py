#!/usr/bin/env python3
"""
VirtualBox compatibility layer for Python 3.13+.

This module provides a Pythonic interface to VirtualBox using VBoxManage
subprocess calls, making it compatible with any Python version.
"""
import json
import logging
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Set up logging
logger = logging.getLogger(__name__)

# Path to VBoxManage (will be detected automatically)
VBOX_MANAGE = "VBoxManage"


class VirtualBoxError(Exception):
    """Base exception for VirtualBox operations."""
    pass


class VBoxManage:
    """Wrapper around VBoxManage command-line tool."""

    def __init__(self, vbox_manage_path: str = None):
        """Initialize the VBoxManage wrapper.
        
        Args:
            vbox_manage_path: Optional path to VBoxManage executable.
                             If not provided, will search in PATH.
        """
        self.vbox_manage = vbox_manage_path or self._find_vbox_manage()
        self._version = None
        self._version_normalized = None
        self._api_version = None

    def _find_vbox_manage(self) -> str:
        """Find VBoxManage in the system PATH."""
        # Check common installation paths on Windows
        common_paths = [
            r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return f'"{path}"'
        
        # Fall back to just 'VBoxManage' and hope it's in PATH
        return "VBoxManage"

    def _run_command(self, command: Union[str, List[str]], parse_json: bool = False) -> Any:
        """Run a VBoxManage command and return the output.
        
        Args:
            command: The VBoxManage command to run (without the 'VBoxManage' prefix)
            parse_json: If True, parse the output as JSON
            
        Returns:
            The command output as a string or parsed JSON
            
        Raises:
            VirtualBoxError: If the command fails
        """
        # Convert command to a list if it's a string
        if isinstance(command, str):
            command = shlex.split(command)
        
        # On Windows, we need to handle the command as a single string
        if isinstance(command, list):
            # Quote arguments that contain spaces
            quoted_command = []
            for arg in command:
                if ' ' in str(arg) and not (str(arg).startswith('"') and str(arg).endswith('"')):
                    quoted_command.append(f'"{arg}"')
                else:
                    quoted_command.append(str(arg))
            
            # Join the command parts with spaces
            full_command = f'{self.vbox_manage} {" ".join(quoted_command)}'
        else:
            full_command = f'{self.vbox_manage} {command}'
        
        logger.debug("Running command: %s", full_command)
        
        try:
            # Use shell=True on Windows to handle the command properly
            result = subprocess.run(
                full_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,  # Required for Windows
                universal_newlines=True
            )
            
            output = result.stdout.strip()
            
            if parse_json:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    raise VirtualBoxError(f"Failed to parse JSON output: {e}") from e
            
            return output
            
        except subprocess.CalledProcessError as e:
            error_msg = f"VBoxManage command failed with code {e.returncode}: {e.stderr}"
            logger.error(error_msg)
            raise VirtualBoxError(error_msg) from e

    @property
    def version(self) -> str:
        """Get the VirtualBox version."""
        if self._version is None:
            self._version = self._run_command("--version")
        return self._version

    @property
    def version_normalized(self) -> str:
        """Get the normalized VirtualBox version."""
        if self._version_normalized is None:
            self._version_normalized = self._run_command("--nologo", "--version")
        return self._version_normalized

    @property
    def api_version(self) -> str:
        """Get the VirtualBox API version."""
        if self._api_version is None:
            # Extract API version from version string (format: major.minor.patch)
            version_parts = self.version.split('.')[:2]
            self._api_version = '.'.join(version_parts)
        return self._api_version

    def list_vms(self, verbose: bool = False) -> List[Dict[str, Any]]:
        """List all registered VMs.
        
        Args:
            verbose: If True, include detailed VM information
            
        Returns:
            List of VM information dictionaries
        """
        if verbose:
            command = ["list", "vms", "--long"]
        else:
            command = ["list", "vms"]
            
        output = self._run_command(command)
        return self._parse_vm_list(output, verbose)
    
    def _parse_vm_list(self, output: str, verbose: bool = False) -> List[Dict[str, Any]]:
        """Parse the output of 'VBoxManage list vms'."""
        vms = []
        current_vm = {}
        
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('"'):
                # New VM entry
                if current_vm:
                    vms.append(current_vm)
                
                # Parse VM name and UUID
                name, uuid = line.split(' ', 1)
                name = name.strip('"')
                uuid = uuid.strip('{}')
                
                current_vm = {
                    'name': name,
                    'uuid': uuid,
                    'state': 'unknown'
                }
            elif verbose and ':' in line:
                # Parse VM property
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                current_vm[key] = value.strip()
        
        # Add the last VM
        if current_vm:
            vms.append(current_vm)
            
        return vms

    def get_vm_info(self, vm_name_or_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific VM.
        
        Args:
            vm_name_or_id: The name or UUID of the VM
            
        Returns:
            Dictionary containing VM information
        """
        command = ["showvminfo", vm_name_or_id, "--machinereadable"]
        output = self._run_command(command)
        
        # Parse the machine-readable output
        info = {}
        for line in output.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.lower()] = value.strip('"')
                
        return info
    
    def start_vm(self, vm_name_or_id: str, headless: bool = False) -> bool:
        """Start a VM.
        
        Args:
            vm_name_or_id: The name or UUID of the VM to start
            headless: If True, start in headless mode
            
        Returns:
            True if the VM was started successfully
        """
        command = ["startvm", vm_name_or_id]
        if headless:
            command.append("--type")
            command.append("headless")
            
        self._run_command(command)
        return True
    
    def stop_vm(self, vm_name_or_id: str, force: bool = False) -> bool:
        """Stop a running VM.
        
        Args:
            vm_name_or_id: The name or UUID of the VM to stop
            force: If True, force stop the VM (equivalent to power off)
            
        Returns:
            True if the VM was stopped successfully
        """
        command = ["controlvm", vm_name_or_id, "poweroff" if force else "acpipowerbutton"]
        self._run_command(command)
        return True
    
    def create_vm(self, name: str, os_type: str, memory_mb: int = 1024, 
                 cpus: int = 1, disk_size_mb: int = 20480) -> Dict[str, Any]:
        """Create a new VM.
        
        Args:
            name: Name of the new VM
            os_type: Operating system type (e.g., 'Windows10_64', 'Ubuntu_64')
            memory_mb: Amount of RAM in MB
            cpus: Number of virtual CPUs
            disk_size_mb: Size of the virtual disk in MB
            
        Returns:
            Dictionary containing information about the created VM
        """
        # Create the VM
        self._run_command(["createvm", "--name", name, "--ostype", os_type, "--register"])
        
        # Configure basic settings
        self._run_command(["modifyvm", name, "--memory", str(memory_mb)])
        self._run_command(["modifyvm", name, "--cpus", str(cpus)])
        
        # Create a virtual disk
        disk_path = str(Path.home() / "VirtualBox VMs" / name / f"{name}.vdi")
        self._run_command([
            "createhd", "--filename", disk_path, "--size", str(disk_size_mb)
        ])
        
        # Attach the disk to the VM
        self._run_command([
            "storageattach", name, "--storagectl", "SATA Controller",
            "--port", "0", "--device", "0", "--type", "hdd",
            "--medium", disk_path
        ])
        
        # Enable some common features
        self._run_command(["modifyvm", name, "--ioapic", "on"])
        self._run_command(["modifyvm", name, "--boot1", "dvd", "--boot2", "disk"])
        
        # Return VM info
        return self.get_vm_info(name)
    
    def delete_vm(self, vm_name_or_id: str, delete_disks: bool = False) -> bool:
        """Delete a VM.
        
        Args:
            vm_name_or_id: The name or UUID of the VM to delete
            delete_disks: If True, also delete all associated disk images
            
        Returns:
            True if the VM was deleted successfully
        """
        command = ["unregistervm", vm_name_or_id]
        if delete_disks:
            command.append("--delete")
            
        self._run_command(command)
        return True


# Singleton instance for convenience
vbox = VBoxManage()


def get_virtualbox() -> VBoxManage:
    """Get the VirtualBox instance."""
    return vbox


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Get VirtualBox instance
        vbox = get_virtualbox()
        # Moved debug info to logs only
        import logging
        logger = logging.getLogger("vboxmcp")
        logger.info(f"VirtualBox Version: {vbox.version}")
        logger.info(f"API Version: {vbox.api_version}")
        
        # List all VMs
        logger.info("List of VMs:")
        vms = vbox.list_vms(verbose=True)
        for i, vm in enumerate(vms, 1):
            logger.info(f"{i}. {vm['name']} (State: {vm.get('state', 'unknown')})")
            
    except VirtualBoxError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
