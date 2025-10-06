"""
VM Template Management Module

This module provides functionality for managing VM templates, including creating
from existing VMs, deploying new VMs from templates, and managing template
lifecycle.
"""

import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def template_operation(func):
    """Decorator for template operations with error handling and logging."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Template operation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation": func.__name__,
                "template": kwargs.get('template_name', 'unknown')
            }
    return wrapper

class VMTemplateMixin:
    """
    Mixin class providing VM template management methods.
    
    This class handles the creation, deployment, and management of VM templates,
    which are essentially pre-configured VM snapshots that can be used to quickly
    deploy new VMs with identical configurations.
    """
    
    # Default template directory (relative to VirtualBox VMs folder)
    TEMPLATE_DIR = "Templates"
    
    def __init__(self, vm_service):
        """
        Initialize with a reference to the parent VMService.
        
        Args:
            vm_service: Reference to the parent VMService instance
        """
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations
        
        # Ensure template directory exists
        self.template_dir = os.path.join(
            self.vbox_manager.vbox.system_properties.default_machine_folder,
            self.TEMPLATE_DIR
        )
        os.makedirs(self.template_dir, exist_ok=True)
    
    @template_operation
    def create_template(self, vm_name: str, template_name: str, 
                       description: str = "", include_disks: bool = True) -> Dict[str, Any]:
        """
        Create a template from an existing virtual machine.
        
        This method creates a template by cloning the specified VM and storing
        its configuration. The template can later be used to deploy new VMs
        with identical configurations.
        
        API Endpoint: POST /templates
        
        Args:
            vm_name: Name of the VM to use as a template
            template_name: Name for the new template
            description: Optional description for the template
            include_disks: Whether to include disk images in the template
                         (default: True)
            
        Returns:
            Dictionary containing the result of the operation and template details
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the VM is not found or if there's an error
                         creating the template
                         
        Example:
            ```python
            # Create a template from an existing VM
            result = templates.create_template(
                vm_name="ubuntu-base",
                template_name="ubuntu-2204-base",
                description="Ubuntu 22.04 LTS with base packages",
                include_disks=True
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not template_name:
            raise ValueError("Template name is required")
        
        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")
        
        # Create template directory
        template_path = os.path.join(self.template_dir, template_name)
        os.makedirs(template_path, exist_ok=True)
        
        try:
            # Export the VM to OVF format
            ovf_path = os.path.join(template_path, f"{template_name}.ovf")
            
            # Create export options
            options = [
                self.vbox_manager.constants.ExportOptions_CreateManifests,
                self.vbox_manager.constants.ExportOptions_ExportDVDImages
            ]
            
            if not include_disks:
                options.append(self.vbox_manager.constants.ExportOptions_ExportIsoImages)
            
            # Export the appliance
            appliance = self.vbox_manager.vbox.create_appliance()
            progress = appliance.write(
                self.vbox_manager.constants.ApplianceFormat_OVF20,
                ovf_path,
                False,  # Write manifest (not needed for templates)
                [str(vm.id)]  # List of machine IDs to export
            )
            
            # Wait for export to complete
            progress.wait_for_completion(-1)
            
            # Save template metadata
            metadata = {
                "name": template_name,
                "description": description,
                "source_vm": vm_name,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "includes_disks": include_disks,
                "ovf_path": f"{template_name}.ovf"
            }
            
            with open(os.path.join(template_path, "metadata.json"), 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Created template '{template_name}' from VM '{vm_name}'",
                "template_name": template_name,
                "template_path": template_path,
                "metadata": metadata
            }
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(template_path):
                shutil.rmtree(template_path, ignore_errors=True)
            raise RuntimeError(f"Failed to create template: {e}")
    
    @template_operation
    def deploy_from_template(self, template_name: str, new_vm_name: str, 
                           **kwargs) -> Dict[str, Any]:
        """
        Deploy a new virtual machine from a template.
        
        This method creates a new VM by importing a previously created template.
        The new VM will have the same configuration as the template.
        
        API Endpoint: POST /templates/{template_name}/deploy
        
        Args:
            template_name: Name of the template to use
            new_vm_name: Name for the new VM
            **kwargs: Additional VM configuration options:
                - memory_mb: Amount of memory in MB (default: from template)
                - cpus: Number of CPUs (default: from template)
                - network: Network configuration (default: from template)
                - start_vm: Whether to start the VM after creation (default: False)
            
        Returns:
            Dictionary containing the result of the operation and new VM details
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the template is not found or if there's an error
                         deploying the VM
                         
        Example:
            ```python
            # Deploy a new VM from a template
            result = templates.deploy_from_template(
                template_name="ubuntu-2204-base",
                new_vm_name="my-new-vm",
                memory_mb=4096,
                cpus=2,
                start_vm=True
            )
            ```
        """
        # Input validation
        if not template_name:
            raise ValueError("Template name is required")
        if not new_vm_name:
            raise ValueError("New VM name is required")
        
        # Check if template exists
        template_path = os.path.join(self.template_dir, template_name)
        if not os.path.isdir(template_path):
            raise RuntimeError(f"Template '{template_name}' not found")
        
        # Load template metadata
        metadata_path = os.path.join(template_path, "metadata.json")
        if not os.path.isfile(metadata_path):
            raise RuntimeError(f"Invalid template: metadata not found in {template_path}")
        
        try:
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Get OVF file path
            ovf_file = os.path.join(template_path, metadata['ovf_path'])
            if not os.path.isfile(ovf_file):
                raise RuntimeError(f"OVF file not found: {ovf_file}")
            
            # Import the appliance
            appliance = self.vbox_manager.vbox.create_appliance()
            progress = appliance.read(ovf_file)
            progress.wait_for_completion(-1)
            
            # Configure import options
            import_options = [
                self.vbox_manager.constants.ImportOptions_KeepAllMACs,
                self.vbox_manager.constants.ImportOptions_KeepNATMACs
            ]
            
            # Import the VM
            progress = appliance.import_machines(import_options)
            progress.wait_for_completion(-1)
            
            # Get the imported VM
            vm = self.vbox_manager.vbox.find_machine(new_vm_name)
            if not vm:
                raise RuntimeError(f"Failed to find imported VM '{new_vm_name}'")
            
            # Apply any overrides from kwargs
            if 'memory_mb' in kwargs:
                vm.memory_size = int(kwargs['memory_mb'])
            if 'cpus' in kwargs:
                vm.CPU_count = int(kwargs['cpus'])
            
            # Save VM settings
            session = self.vbox_manager.mgr.get_session_object()
            try:
                vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)
                session.machine.save_settings()
            finally:
                session.unlock_machine()
            
            # Start the VM if requested
            start_vm = kwargs.get('start_vm', False)
            if start_vm:
                self.vm_operations.start_vm(new_vm_name)
            
            return {
                "status": "success",
                "message": f"Deployed VM '{new_vm_name}' from template '{template_name}'",
                "vm_name": new_vm_name,
                "template_name": template_name,
                "started": start_vm,
                "vm_id": vm.id
            }
            
        except Exception as e:
            # Clean up if VM was partially created
            vm = self.vbox_manager.vbox.find_machine(new_vm_name)
            if vm:
                # Use unregister mode 1 (delete all files)
                vm.unregister(1)
            raise RuntimeError(f"Failed to deploy VM from template: {e}")
    
    @template_operation
    def list_templates(self) -> Dict[str, Any]:
        """List all available VM templates."""
        try:
            # Get all templates
            templates = []
            for template_name in os.listdir(self.template_dir):
                template_path = os.path.join(self.template_dir, template_name)
                if os.path.isdir(template_path):
                    metadata_path = os.path.join(template_path, "metadata.json")
                    if os.path.isfile(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            templates.append(metadata)
            
            return {
                "status": "success",
                "templates": templates
            }
        except Exception as e:
            logger.error(f"Failed to list templates: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def delete_template(self, template_name: str) -> Dict[str, Any]:
        """Delete a VM template."""
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to delete template {template_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}



