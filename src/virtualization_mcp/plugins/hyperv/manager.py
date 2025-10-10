"""
Hyper-V Manager Plugin for virtualization-mcp

This module provides Hyper-V VM management functionality.
"""
import asyncio
import logging
import platform
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class VMState(str, Enum):
    RUNNING = "Running"
    OFF = "Off"
    STARTING = "Starting"
    STOPPING = "Stopping"
    SAVED = "Saved"
    PAUSED = "Paused"
    ERROR = "Error"

class VMSize(BaseModel):
    memory_mb: int = Field(..., description="Memory in MB")
    cpu_count: int = Field(..., description="Number of CPUs")
    disk_size_gb: int = Field(..., description="Disk size in GB")

class VMDisk(BaseModel):
    path: str = Field(..., description="Path to the disk file")
    size_gb: int = Field(..., description="Size in GB")
    type: str = Field("VHDX", description="Disk type (VHD/VHDX)")

class VMSnapshot(BaseModel):
    name: str = Field(..., description="Snapshot name")
    id: str = Field(..., description="Snapshot ID")
    creation_time: str = Field(..., description="Creation timestamp")

class VMNetworkAdapter(BaseModel):
    name: str = Field(..., description="Adapter name")
    switch_name: str = Field(..., description="Virtual switch name")
    mac_address: str = Field(..., description="MAC address")
    enabled: bool = Field(True, description="Whether the adapter is enabled")

class VirtualMachine(BaseModel):
    name: str = Field(..., description="VM name")
    id: str = Field(..., description="VM unique ID")
    state: VMState = Field(..., description="Current VM state")
    path: str = Field(..., description="VM configuration path")
    size: VMSize = Field(..., description="VM resource allocation")
    disks: List[VMDisk] = Field(default_factory=list, description="Attached disks")
    snapshots: List[VMSnapshot] = Field(default_factory=list, description="VM snapshots")
    network_adapters: List[VMNetworkAdapter] = Field(
        default_factory=list, 
        description="Network adapters"
    )

class HyperVManagerPlugin:
    """Hyper-V Manager Plugin for virtualization-mcp."""
    
    def __init__(self):
        self.mcp = None
        self.initialized = False
        
    async def initialize(self, mcp: FastMCP) -> None:
        """Initialize the Hyper-V plugin."""
        if self.initialized:
            return
            
        self.mcp = mcp
        self.initialized = True
        logger.info("Hyper-V Manager Plugin initialized")
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register Hyper-V tools with FastMCP."""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized. Call initialize() first.")
            
        @mcp.tool("list_hyperv_vms")
        async def list_hyperv_vms() -> List[Dict[str, Any]]:
            """List all Hyper-V virtual machines."""
            # Implementation will use powershell to list VMs
            return await self._list_vms()
            
        @mcp.tool("get_hyperv_vm")
        async def get_hyperv_vm(vm_name: str) -> Dict[str, Any]:
            """Get details about a specific Hyper-V VM.
            
            Args:
                vm_name: Name of the VM to retrieve
            """
            return await self._get_vm(vm_name)
            
        @mcp.tool("start_hyperv_vm")
        async def start_hyperv_vm(vm_name: str) -> Dict[str, Any]:
            """Start a Hyper-V virtual machine.
            
            Args:
                vm_name: Name of the VM to start
            """
            return await self._start_vm(vm_name)
            
        @mcp.tool("stop_hyperv_vm")
        async def stop_hyperv_vm(vm_name: str, force: bool = False) -> Dict[str, Any]:
            """Stop a Hyper-V virtual machine.
            
            Args:
                vm_name: Name of the VM to stop
                force: Whether to force stop the VM
            """
            return await self._stop_vm(vm_name, force)
    
    # Implementation methods
    async def _list_vms(self) -> List[Dict[str, Any]]:
        """List all Hyper-V VMs."""
        # Implementation using powershell
        cmd = "Get-VM | Select-Object Name, State, Uptime, Status | ConvertTo-Json"
        try:
            proc = await asyncio.create_subprocess_shell(
                f"powershell -Command \"{cmd}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to list VMs: {stderr.decode()}")
                
            return []  # Parse and return VM list
            
        except Exception as e:
            logger.error(f"Error listing VMs: {e}")
            raise
    
    # Other implementation methods would follow the same pattern
    async def _get_vm(self, vm_name: str) -> Dict[str, Any]:
        """Get VM details."""
        raise NotImplementedError
        
    async def _start_vm(self, vm_name: str) -> Dict[str, Any]:
        """Start a VM."""
        raise NotImplementedError
        
    async def _stop_vm(self, vm_name: str, force: bool = False) -> Dict[str, Any]:
        """Stop a VM."""
        raise NotImplementedError



