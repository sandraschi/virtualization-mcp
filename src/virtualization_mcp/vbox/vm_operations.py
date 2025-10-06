"""
VM Operations - Virtual Machine lifecycle management

Handles create, start, stop, delete, and configuration operations
using a compatibility layer that works with both VirtualBox Python API
and VBoxManage command-line tool.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from .compat_adapter import VBoxManager, VBoxManagerError

logger = logging.getLogger(__name__)


class VMOperations:
    """
    High-level VM lifecycle operations
    
    Provides Austrian dev efficiency with comprehensive VM management
    including template-based creation, state management, and configuration.
    """
    
    def __init__(self, manager: VBoxManager, templates_path: Optional[Union[str, Path]] = None):
        """
        Initialize VM operations with compatibility layer
        
        Args:
            manager: VBoxManager instance (from compat_adapter)
            templates_path: Path to VM templates YAML file or directory
        """
        self.manager = manager
        
        # Handle templates path resolution
        if templates_path is None:
            # Default to config directory in the package
            self.templates_path = Path(__file__).parent.parent.parent / 'config' / 'vm_templates.yaml'
        else:
            self.templates_path = Path(templates_path)
            
        self._templates = None
        logger.debug(f"VMOperations initialized with templates path: {self.templates_path}")
    
    @property
    def templates(self) -> Dict[str, Any]:
        """Load and cache VM templates"""
        if self._templates is None:
            self._templates = self._load_templates()
        return self._templates
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load VM templates from YAML file"""
        try:
            if self.templates_path.exists():
                with open(self.templates_path, 'r') as f:
                    data = yaml.safe_load(f)
                    return data.get('templates', {})
            else:
                logger.warning(f"Templates file not found: {self.templates_path}")
                return self._get_default_templates()
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Return default VM templates if file loading fails"""
        return {
            "ubuntu-dev": {
                "os_type": "Ubuntu_64",
                "memory_mb": 4096,
                "disk_gb": 25,
                "network": "NAT",
                "description": "Ubuntu development environment"
            },
            "minimal-linux": {
                "os_type": "Ubuntu_64", 
                "memory_mb": 1024,
                "disk_gb": 10,
                "network": "NAT",
                "description": "Minimal Linux for quick tests"
            }
        }
    
    def create_vm(self, name: str, template: str = "ubuntu-dev", 
                  memory_mb: Optional[int] = None, 
                  disk_gb: Optional[int] = None,
                  custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create new VM from template with optional overrides
        
        Args:
            name: VM name
            template: Template name from config
            memory_mb: Override template memory
            disk_gb: Override template disk size
            custom_settings: Additional custom settings
            
        Returns:
            Dict with creation result and VM info
        """
        try:
            # Validate VM name
            if not self.manager.validate_vm_name(name):
                raise VBoxManagerError(f"Invalid VM name: '{name}'")
            
            # Check if VM already exists
            if self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' already exists")
            
            # Get template configuration
            if template not in self.templates:
                raise VBoxManagerError(f"Template '{template}' not found. Available: {list(self.templates.keys())}")
            
            template_config = self.templates[template].copy()
            
            # Apply overrides
            if memory_mb:
                template_config["memory_mb"] = memory_mb
            if disk_gb:
                template_config["disk_gb"] = disk_gb
            if custom_settings:
                template_config.update(custom_settings)
            
            logger.info(f"Creating VM '{name}' from template '{template}'")
            
            # Create VM
            self.manager.run_command([
                "createvm",
                "--name", name,
                "--ostype", template_config["os_type"],
                "--register"
            ])
            
            # Configure memory
            self.manager.run_command([
                "modifyvm", name,
                "--memory", str(template_config["memory_mb"])
            ])
            
            # Configure network
            network_type = template_config.get("network", "NAT")
            self.manager.run_command([
                "modifyvm", name,
                "--nic1", network_type.lower()
            ])
            
            # Create and attach disk if specified
            if template_config.get("disk_gb"):
                disk_path = self._create_disk(name, template_config["disk_gb"])
                self._attach_disk(name, disk_path)
            
            # Apply additional settings
            self._apply_vm_settings(name, template_config)
            
            # Get final VM info
            vm_info = self.manager.get_vm_info(name)
            
            result = {
                "success": True,
                "vm_name": name,
                "template": template,
                "configuration": template_config,
                "vm_info": vm_info,
                "message": f"VM '{name}' created successfully from template '{template}'"
            }
            
            logger.info(f"Successfully created VM '{name}'")
            return result
            
        except VBoxManagerError as e:
            logger.error(f"Failed to create VM '{name}': {e}")
            # Cleanup on failure
            self._cleanup_failed_vm(name)
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating VM '{name}': {e}")
            self._cleanup_failed_vm(name)
            raise VBoxManagerError(f"Failed to create VM: {str(e)}")
    
    def _create_disk(self, vm_name: str, size_gb: int) -> str:
        """Create virtual disk for VM"""
        disk_name = f"{vm_name}.vdi"
        size_mb = size_gb * 1024
        
        self.manager.run_command([
            "createhd",
            "--filename", disk_name,
            "--size", str(size_mb),
            "--format", "VDI"
        ])
        
        return disk_name
    
    def _attach_disk(self, vm_name: str, disk_path: str) -> None:
        """Attach disk to VM"""
        # Add SATA controller
        self.manager.run_command([
            "storagectl", vm_name,
            "--name", "SATA",
            "--add", "sata",
            "--controller", "IntelAHCI"
        ])
        
        # Attach disk
        self.manager.run_command([
            "storageattach", vm_name,
            "--storagectl", "SATA",
            "--port", "0",
            "--device", "0",
            "--type", "hdd",
            "--medium", disk_path
        ])
    
    def _apply_vm_settings(self, vm_name: str, config: Dict[str, Any]) -> None:
        """Apply additional VM settings from template"""
        settings = []
        
        # Enable ACPI and IOAPIC for better compatibility
        settings.extend(["--acpi", "on", "--ioapic", "on"])
        
        # Enable VT-x/AMD-V if available
        settings.extend(["--hwvirtex", "on"])
        
        # Configure video memory
        settings.extend(["--vram", "128"])
        
        # Enable 3D acceleration if supported
        settings.extend(["--accelerate3d", "on"])
        
        # Apply clipboard and drag-n-drop
        settings.extend(["--clipboard", "bidirectional"])
        settings.extend(["--draganddrop", "bidirectional"])
        
        if settings:
            self.manager.run_command(["modifyvm", vm_name] + settings)
    
    def start_vm(self, name: str, headless: bool = True) -> Dict[str, Any]:
        """
        Start virtual machine
        
        Args:
            name: VM name
            headless: Start without GUI (default for testing)
            
        Returns:
            Dict with start result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")
            
            current_state = self.manager.get_vm_state(name)
            if current_state == "running":
                return {
                    "success": True,
                    "vm_name": name,
                    "message": f"VM '{name}' already running",
                    "state": "running"
                }
            
            start_type = "headless" if headless else "gui"
            logger.info(f"Starting VM '{name}' in {start_type} mode")
            
            self.manager.run_command(["startvm", name, "--type", start_type])
            
            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' started successfully",
                "mode": start_type,
                "state": "running"
            }
            
        except VBoxManagerError as e:
            logger.error(f"Failed to start VM '{name}': {e}")
            raise
    
    def stop_vm(self, name: str, force: bool = False) -> Dict[str, Any]:
        """
        Stop virtual machine
        
        Args:
            name: VM name
            force: Force stop (power off) vs graceful shutdown
            
        Returns:
            Dict with stop result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")
            
            current_state = self.manager.get_vm_state(name)
            if current_state != "running":
                return {
                    "success": True,
                    "vm_name": name,
                    "message": f"VM '{name}' already stopped",
                    "state": current_state
                }
            
            stop_type = "poweroff" if force else "acpipowerbutton"
            logger.info(f"Stopping VM '{name}' with {stop_type}")
            
            self.manager.run_command(["controlvm", name, stop_type])
            
            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' stopped successfully",
                "method": "forced" if force else "graceful",
                "state": "poweroff"
            }
            
        except VBoxManagerError as e:
            logger.error(f"Failed to stop VM '{name}': {e}")
            raise
    
    def delete_vm(self, name: str, delete_disk: bool = True) -> Dict[str, Any]:
        """
        Delete virtual machine
        
        Args:
            name: VM name
            delete_disk: Also delete VM disk files
            
        Returns:
            Dict with deletion result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")
            
            # Stop VM if running
            current_state = self.manager.get_vm_state(name)
            if current_state == "running":
                logger.info(f"Stopping running VM '{name}' before deletion")
                self.stop_vm(name, force=True)
            
            # Unregister and delete
            cmd = ["unregistervm", name]
            if delete_disk:
                cmd.append("--delete")
                
            logger.info(f"Deleting VM '{name}' (delete_disk={delete_disk})")
            self.manager.run_command(cmd)
            
            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' deleted successfully",
                "disk_deleted": delete_disk
            }
            
        except VBoxManagerError as e:
            logger.error(f"Failed to delete VM '{name}': {e}")
            raise
    
    def _cleanup_failed_vm(self, name: str) -> None:
        """Clean up VM after failed creation"""
        try:
            if self.manager.vm_exists(name):
                logger.info(f"Cleaning up failed VM '{name}'")
                self.delete_vm(name, delete_disk=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup VM '{name}': {e}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Get list of available VM templates"""
        return [
            {
                "name": name,
                "description": config.get("description", "No description"),
                "os_type": config.get("os_type", "Unknown"),
                "memory_mb": config.get("memory_mb", 0),
                "disk_gb": config.get("disk_gb", 0),
                "config": config
            }
            for name, config in self.templates.items()
        ]
