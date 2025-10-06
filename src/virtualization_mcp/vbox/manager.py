"""
VirtualBox Manager - CLI wrapper for VBoxManage operations
Provides robust, error-handled interface to VirtualBox CLI
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import re

logger = logging.getLogger(__name__)


class VBoxManagerError(Exception):
    """Custom exception for VirtualBox operations"""
    def __init__(self, message: str, command: List[str] = None, return_code: int = None):
        super().__init__(message)
        self.command = command
        self.return_code = return_code


class VBoxManager:
    """
    Robust VBoxManage CLI wrapper with comprehensive error handling
    
    Handles all VirtualBox operations with proper validation,
    error reporting, and Austrian dev efficiency standards.
    """
    
    def __init__(self, vboxmanage_path: str = None):
        """
        Initialize VBoxManager
        
        Args:
            vboxmanage_path: Optional path to VBoxManage executable. If not provided,
                           will attempt to find it automatically.
        """
        self.vboxmanage_path = vboxmanage_path or self._find_vboxmanage()
        self._validate_vboxmanage()
        
    def _find_vboxmanage(self) -> str:
        """
        Attempt to find VBoxManage executable in common locations.
        
        Returns:
            str: Path to VBoxManage executable
            
        Raises:
            VBoxManagerError: If VBoxManage cannot be found
        """
        import os
        import sys
        
        # Common installation paths on Windows
        common_paths = [
            r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files\VirtualBox\VBoxManage.exe",
        ]
        
        # Check if VBoxManage is in PATH
        if sys.platform == 'win32':
            path_exts = os.environ.get('PATHEXT', '').split(os.pathsep)
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            
            for ext in path_exts:
                exe_name = f"VBoxManage{ext}"
                for path_dir in path_dirs:
                    if not path_dir:
                        continue
                    exe_path = os.path.join(path_dir, exe_name)
                    if os.path.isfile(exe_path):
                        logger.info(f"Found VBoxManage in PATH: {exe_path}")
                        return exe_path
        
        # Check common installation paths
        for path in common_paths:
            if os.path.isfile(path):
                logger.info(f"Found VBoxManage at common location: {path}")
                return path
                
        # If we get here, we couldn't find VBoxManage
        raise VBoxManagerError(
            "VBoxManage not found. Please ensure VirtualBox is installed and "
            "either add it to your PATH or specify the full path to VBoxManage."
        )
    
    def _validate_vboxmanage(self) -> None:
        """Validate VBoxManage is available and working"""
        try:
            result = self.run_command(["--version"])
            logger.info(f"VBoxManage available: {result.get('output', 'Unknown version')}")
        except VBoxManagerError:
            raise VBoxManagerError(
                f"VBoxManage not found at '{self.vboxmanage_path}'. "
                "Ensure VirtualBox is installed and in PATH."
            )
    
    def run_command(self, args: List[str], capture_json: bool = False) -> Dict[str, Any]:
        """
        Execute VBoxManage command with robust error handling
        
        Args:
            args: Command arguments (without 'VBoxManage')
            capture_json: Attempt to parse output as JSON
            
        Returns:
            Dict with success, output, error info
            
        Raises:
            VBoxManagerError: On command failure
        """
        cmd = [self.vboxmanage_path] + args
        
        try:
            logger.debug(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                check=False
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown VBoxManage error"
                raise VBoxManagerError(
                    f"VBoxManage failed: {error_msg}",
                    command=cmd,
                    return_code=result.returncode
                )
            
            output = result.stdout.strip()
            
            # Parse JSON output if requested and possible
            parsed_output = output
            if capture_json and output:
                try:
                    parsed_output = json.loads(output)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON output: {output[:100]}...")
            
            return {
                "success": True,
                "output": parsed_output,
                "raw_output": output,
                "command": cmd
            }
            
        except subprocess.TimeoutExpired:
            raise VBoxManagerError(
                f"VBoxManage command timed out after 60 seconds",
                command=cmd
            )
        except FileNotFoundError:
            raise VBoxManagerError(
                f"VBoxManage executable not found: {self.vboxmanage_path}",
                command=cmd
            )
        except Exception as e:
            raise VBoxManagerError(
                f"Unexpected error running VBoxManage: {str(e)}",
                command=cmd
            )
    
    def list_vms(self, state_filter: str = "all") -> List[Dict[str, str]]:
        """
        List virtual machines with optional state filtering
        
        Args:
            state_filter: "all", "running", "stopped", "saved"
            
        Returns:
            List of VM info dicts
        """
        try:
            # Get VM list with details
            if state_filter == "running":
                result = self.run_command(["list", "runningvms"])
            elif state_filter == "stopped":
                # Get all VMs, then filter out running ones
                all_result = self.run_command(["list", "vms"])
                running_result = self.run_command(["list", "runningvms"])
                
                all_vms = self._parse_vm_list(all_result["output"])
                running_vms = {vm["name"] for vm in self._parse_vm_list(running_result["output"])}
                
                return [vm for vm in all_vms if vm["name"] not in running_vms]
            else:
                result = self.run_command(["list", "vms"])
            
            return self._parse_vm_list(result["output"])
            
        except VBoxManagerError as e:
            logger.error(f"Failed to list VMs: {e}")
            raise
    
    def _parse_vm_list(self, output: str) -> List[Dict[str, str]]:
        """Parse VBoxManage VM list output into structured data"""
        vms = []
        for line in output.split('\n'):
            if line.strip():
                # Parse: "VM Name" {uuid}
                match = re.match(r'"([^"]+)"\s+\{([^}]+)\}', line)
                if match:
                    vms.append({
                        "name": match.group(1),
                        "uuid": match.group(2),
                        "state": "unknown"  # Will be filled by get_vm_info if needed
                    })
        return vms
    
    def get_vm_info(self, vm_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific VM"""
        try:
            result = self.run_command(["showvminfo", vm_name, "--machinereadable"])
            return self._parse_machine_readable(result["output"])
        except VBoxManagerError as e:
            if "not find" in str(e).lower():
                raise VBoxManagerError(f"VM '{vm_name}' not found")
            raise
    
    def _parse_machine_readable(self, output: str) -> Dict[str, Any]:
        """Parse VBoxManage machine-readable output into dict"""
        info = {}
        for line in output.split('\n'):
            if '=' in line and line.strip():
                key, value = line.split('=', 1)
                # Remove quotes from values
                value = value.strip('"')
                info[key] = value
        return info
    
    def vm_exists(self, vm_name: str) -> bool:
        """Check if VM exists"""
        try:
            self.get_vm_info(vm_name)
            return True
        except VBoxManagerError:
            return False
    
    def get_vm_state(self, vm_name: str) -> str:
        """Get current state of VM"""
        try:
            info = self.get_vm_info(vm_name)
            return info.get("VMState", "unknown").lower()
        except VBoxManagerError:
            return "notfound"
    
    def validate_vm_name(self, name: str) -> bool:
        """Validate VM name meets VirtualBox requirements"""
        if not name or len(name.strip()) == 0:
            return False
        
        # Basic validation - no problematic characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return not any(char in name for char in invalid_chars)
    
    def get_host_info(self) -> Dict[str, Any]:
        """Get VirtualBox host system information"""
        try:
            result = self.run_command(["list", "hostinfo"])
            return self._parse_host_info(result["output"])
        except VBoxManagerError as e:
            logger.error(f"Failed to get host info: {e}")
            raise
    
    def _parse_host_info(self, output: str) -> Dict[str, Any]:
        """Parse host info output"""
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info
