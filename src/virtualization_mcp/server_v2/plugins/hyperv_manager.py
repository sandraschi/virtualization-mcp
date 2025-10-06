"""Advanced Hyper-V Management plugin for virtualization-mcp."""
import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Deque, Tuple, Union

import aiofiles
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException, status, WebSocket, BackgroundTasks
from pydantic import BaseModel, Field, field_validator, HttpUrl

from virtualization_mcp.server_v2.plugins.base import BasePlugin
from virtualization_mcp.server_v2.plugins import register_plugin

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
    memory_startup: int = Field(2048, description="Startup memory in MB")
    memory_minimum: int = Field(512, description="Minimum dynamic memory in MB")
    memory_maximum: int = Field(8192, description="Maximum dynamic memory in MB")
    processor_count: int = Field(2, description="Number of virtual processors")
    dynamic_memory: bool = Field(True, description="Enable dynamic memory allocation")

class VMDisk(BaseModel):
    path: str
    size_gb: int
    type: str = "VHDX"
    controller_type: str = "SCSI"
    controller_number: int = 0
    controller_location: int = 0

class VMSnapshot(BaseModel):
    name: str
    id: str
    creation_time: datetime
    parent_snapshot_id: Optional[str] = None
    notes: Optional[str] = None
    is_current: bool = False

class VMNetworkAdapter(BaseModel):
    name: str
    switch_name: str
    mac_address: Optional[str] = None
    vlan_id: Optional[int] = None
    is_legacy: bool = False
    static_mac_address: bool = False
    device_naming: str = "On"
    dhcp_guard: str = "Off"
    router_guard: str = "Off"
    port_mirroring: str = "None"
    ieee_priority_tag: str = "Off"
    vmmq_enabled: bool = False
    vmmq_queue_pairs: int = 16
    vmmq_weight: int = 100

class VirtualMachine(BaseModel):
    name: str
    id: str
    state: VMState
    status: str
    cpu_usage: int = 0
    memory_assigned: int = 0
    uptime: Optional[timedelta] = None
    version: str = "9.0"
    generation: int = 2
    path: str
    checkpoint_type: str = "Production"
    automatic_start_action: str = "StartIfRunning"
    automatic_stop_action: str = "Save"
    smart_paging_file_path: str = ""
    snapshot_file_location: str = ""
    configuration_location: str = ""
    notes: str = ""
    creation_time: Optional[datetime] = None
    dynamic_memory_enabled: bool = True
    secure_boot_enabled: bool = True
    tpm_enabled: bool = False
    nested_virtualization: bool = False
    automatic_checkpoints_enabled: bool = True
    checkpoint_id: Optional[str] = None
    computer_name: Optional[str] = None
    operating_system: Optional[str] = None
    size: VMSize = Field(default_factory=VMSize)
    disks: List[VMDisk] = []
    network_adapters: List[VMNetworkAdapter] = []
    snapshots: List[VMSnapshot] = []
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class HyperVManagerPlugin(BasePlugin):
    """Advanced Hyper-V Management plugin for virtualization-mcp."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.hyperv_host = config.get("host", "localhost")
        self.vm_export_path = Path(config.get("export_path", "C:\\HyperV\\Exports"))
        self.vm_import_path = Path(config.get("import_path", "C:\\HyperV\\Imports"))
        self.backup_path = Path(config.get("backup_path", "C:\\HyperV\\Backups"))
        self.template_path = Path(config.get("template_path", "C:\\HyperV\\Templates"))
        
        # Ensure directories exist
        self.vm_export_path.mkdir(parents=True, exist_ok=True)
        self.vm_import_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.template_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.virtual_machines: Dict[str, VirtualMachine] = {}
        self.virtual_switches: List[Dict[str, Any]] = []
        self.background_tasks: Dict[str, asyncio.Task] = {}
        self.event_listeners: Dict[str, asyncio.Task] = {}
        self.websockets: List[WebSocket] = []
        
        # Performance metrics
        self.performance_metrics: Dict[str, Any] = {
            "cpu_usage": [],
            "memory_usage": [],
            "network_throughput": [],
            "disk_io": []
        }
        
        # Set up routes
        self.setup_routes()
        
        # Initialize Hyper-V module
        self._check_hyperv_module()
    
    def _check_hyperv_module(self) -> None:
        """Check if Hyper-V module is available and import it."""
        try:
            import hyperv
            self.hyperv = hyperv
            logger.info("Hyper-V module imported successfully")
        except ImportError:
            logger.warning(
                "Hyper-V module not found. Using PowerShell commands instead. "
                "For better performance, install the 'hyperv' package: "
                "pip install hyperv"
            )
            self.hyperv = None
    
    def setup_routes(self) -> None:
        """Set up API routes for Hyper-V management."""
        @self.router.get("/vms", response_model=List[VirtualMachine])
        async def list_vms() -> List[VirtualMachine]:
            """List all virtual machines."""
            await self._refresh_vm_list()
            return list(self.virtual_machines.values())
        
        @self.router.get("/vms/{vm_name}", response_model=VirtualMachine)
        async def get_vm(vm_name: str) -> VirtualMachine:
            """Get details of a specific virtual machine."""
            await self._refresh_vm_list()
            if vm_name not in self.virtual_machines:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Virtual machine '{vm_name}' not found"
                )
            return self.virtual_machines[vm_name]
        
        @self.router.post("/vms/{vm_name}/start")
        async def start_vm(vm_name: str, wait: bool = False) -> Dict[str, Any]:
            """Start a virtual machine."""
            return await self._execute_vm_action("start", vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/stop")
        async def stop_vm(vm_name: str, force: bool = False, wait: bool = False) -> Dict[str, Any]:
            """Stop a virtual machine."""
            action = "stop" if not force else "force_stop"
            return await self._execute_vm_action(action, vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/restart")
        async def restart_vm(vm_name: str, force: bool = False, wait: bool = False) -> Dict[str, Any]:
            """Restart a virtual machine."""
            action = "restart" if not force else "force_restart"
            return await self._execute_vm_action(action, vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/save")
        async def save_vm(vm_name: str, wait: bool = False) -> Dict[str, Any]:
            """Save the state of a virtual machine."""
            return await self._execute_vm_action("save", vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/suspend")
        async def suspend_vm(vm_name: str, wait: bool = False) -> Dict[str, Any]:
            """Suspend a virtual machine."""
            return await self._execute_vm_action("suspend", vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/resume")
        async def resume_vm(vm_name: str, wait: bool = False) -> Dict[str, Any]:
            """Resume a suspended virtual machine."""
            return await self._execute_vm_action("resume", vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/reset")
        async def reset_vm(vm_name: str, wait: bool = False) -> Dict[str, Any]:
            """Reset a virtual machine."""
            return await self._execute_vm_action("reset", vm_name, wait)
        
        @self.router.post("/vms/{vm_name}/export")
        async def export_vm(
            vm_name: str,
            export_path: str = None,
            compress: bool = True,
            wait: bool = False
        ) -> Dict[str, Any]:
            """Export a virtual machine."""
            if not export_path:
                export_path = str(self.vm_export_path / f"{vm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            return await self._execute_vm_action(
                "export", 
                vm_name, 
                wait,
                export_path=export_path,
                compress=compress
            )
        
        @self.router.post("/vms/import")
        async def import_vm(
            name: str,
            import_path: str,
            vhd_path: str = None,
            generate_new_id: bool = True,
            wait: bool = False
        ) -> Dict[str, Any]:
            """Import a virtual machine."""
            task_id = f"import_{name}_{int(time.time())}"
            
            async def _import_task() -> Dict[str, Any]:
                try:
                    # In a real implementation, this would use Hyper-V's import functionality
                    # For now, we'll simulate the import
                    await asyncio.sleep(5)  # Simulate import time
                    
                    # Add the new VM to our list
                    await self._refresh_vm_list()
                    
                    return {
                        "status": "completed",
                        "vm_name": name,
                        "import_path": import_path,
                        "message": f"Successfully imported VM '{name}'"
                    }
                except Exception as e:
                    logger.error(f"Error importing VM: {str(e)}", exc_info=True)
                    raise
            
            # Start the import task
            task = asyncio.create_task(_import_task())
            self.background_tasks[task_id] = task
            
            # Clean up the task when done
            task.add_done_callback(lambda t: self.background_tasks.pop(task_id, None))
            
            if wait:
                return await task
            
            return {
                "status": "started",
                "task_id": task_id,
                "message": f"Import of VM '{name}' has started"
            }
        
        @self.router.post("/vms/{vm_name}/snapshot")
        async def create_snapshot(
            vm_name: str,
            snapshot_name: str,
            description: str = "",
            wait: bool = False
        ) -> Dict[str, Any]:
            """Create a snapshot of a virtual machine."""
            return await self._execute_vm_action(
                "create_snapshot",
                vm_name,
                wait,
                snapshot_name=snapshot_name,
                description=description
            )
        
        @self.router.get("/vms/{vm_name}/snapshots")
        async def list_snapshots(vm_name: str) -> List[Dict[str, Any]]:
            """List all snapshots for a virtual machine."""
            await self._refresh_vm_list()
            if vm_name not in self.virtual_machines:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Virtual machine '{vm_name}' not found"
                )
            
            return [s.dict() for s in self.virtual_machines[vm_name].snapshots]
        
        @self.router.post("/vms/{vm_name}/restore")
        async def restore_snapshot(
            vm_name: str,
            snapshot_id: str,
            wait: bool = False
        ) -> Dict[str, Any]:
            """Restore a virtual machine to a specific snapshot."""
            return await self._execute_vm_action(
                "restore_snapshot",
                vm_name,
                wait,
                snapshot_id=snapshot_id
            )
        
        @self.router.delete("/vms/{vm_name}/snapshots/{snapshot_id}")
        async def delete_snapshot(
            vm_name: str,
            snapshot_id: str,
            wait: bool = False
        ) -> Dict[str, Any]:
            """Delete a snapshot."""
            return await self._execute_vm_action(
                "delete_snapshot",
                vm_name,
                wait,
                snapshot_id=snapshot_id
            )
        
        @self.router.get("/switches")
        async def list_switches() -> List[Dict[str, Any]]:
            """List all virtual switches."""
            await self._refresh_switches()
            return self.virtual_switches
        
        @self.router.websocket("/ws/events")
        async def websocket_events(websocket: WebSocket):
            """WebSocket endpoint for real-time events."""
            await websocket.accept()
            self.websockets.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
            finally:
                if websocket in self.websockets:
                    self.websockets.remove(websocket)
    
    async def _execute_vm_action(
        self,
        action: str,
        vm_name: str,
        wait: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a VM action and return the result."""
        task_id = f"{action}_{vm_name}_{int(time.time())}"
        
        async def _action_task() -> Dict[str, Any]:
            try:
                # In a real implementation, this would use Hyper-V's API
                # For now, we'll simulate the action
                logger.info(f"Executing action '{action}' on VM '{vm_name}' with args: {kwargs}")
                
                # Simulate action taking some time
                await asyncio.sleep(2)
                
                # Update VM state
                await self._refresh_vm_list()
                
                return {
                    "status": "completed",
                    "action": action,
                    "vm_name": vm_name,
                    "message": f"Successfully executed '{action}' on VM '{vm_name}'",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Error executing action '{action}' on VM '{vm_name}': {str(e)}", exc_info=True)
                raise
        
        # Start the action task
        task = asyncio.create_task(_action_task())
        self.background_tasks[task_id] = task
        
        # Clean up the task when done
        task.add_done_callback(lambda t: self.background_tasks.pop(task_id, None))
        
        if wait:
            return await task
        
        return {
            "status": "started",
            "task_id": task_id,
            "action": action,
            "vm_name": vm_name,
            "message": f"Action '{action}' has started on VM '{vm_name}'",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _refresh_vm_list(self) -> None:
        """Refresh the list of virtual machines from Hyper-V."""
        # In a real implementation, this would query Hyper-V for the list of VMs
        # For now, we'll return a static list for demonstration
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Query Hyper-V for the list of VMs
        # 2. For each VM, get its details (state, configuration, etc.)
        # 3. Update self.virtual_machines with the current state
        
        # Example VM (simulated)
        if not self.virtual_machines:
            self.virtual_machines["TestVM"] = VirtualMachine(
                name="TestVM",
                id="00000000-0000-0000-0000-000000000000",
                state=VMState.OFF,
                status="Operating normally",
                path="C:\\VMs\\TestVM",
                creation_time=datetime.utcnow(),
                size=VMSize()
            )
    
    async def _refresh_switches(self) -> None:
        """Refresh the list of virtual switches from Hyper-V."""
        # In a real implementation, this would query Hyper-V for the list of switches
        # For now, we'll return a static list for demonstration
        if not self.virtual_switches:
            self.virtual_switches = [
                {
                    "name": "Default Switch",
                    "id": "00000000-0000-0000-0000-000000000001",
                    "type": "Internal",
                    "net_adapter_interface_description": "Hyper-V Virtual Ethernet Adapter",
                    "iov_enabled": True,
                    "iov_queue_pairs_requested": 16,
                    "iov_interrupt_moderation": "Off",
                    "iov_weight": 100,
                    "bandwidth_reservation_mode": "Default",
                    "default_flow_minimum_bandwidth_absolute": 0,
                    "default_flow_minimum_bandwidth_weight": 0,
                    "default_queue_vmmq_enabled": False,
                    "default_queue_vmmq_queue_pairs": 16,
                    "default_queue_vrss_enabled": True,
                    "default_queue_vrss_min_queue_pairs": 1,
                    "default_queue_vrss_max_queue_pairs": 16,
                    "default_queue_vrss_queue_scheduling_interval": 100,
                    "default_queue_vrss_independent_host_spreading": False
                }
            ]
    
    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected WebSocket clients."""
        if not self.websockets:
            return
        
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        for websocket in list(self.websockets):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {str(e)}")
                if websocket in self.websockets:
                    self.websockets.remove(websocket)
    
    async def _monitor_performance(self) -> None:
        """Monitor Hyper-V host and VM performance."""
        while True:
            try:
                # In a real implementation, this would collect performance counters
                # For now, we'll simulate some metrics
                metrics = {
                    "cpu_usage": 25.5,  # %
                    "memory_usage": 60.2,  # %
                    "network_in": 1024 * 1024,  # bytes/s
                    "network_out": 512 * 1024,  # bytes/s
                    "disk_read": 5 * 1024 * 1024,  # bytes/s
                    "disk_write": 2 * 1024 * 1024  # bytes/s
                }
                
                # Update metrics history
                timestamp = datetime.utcnow().isoformat()
                for key, value in metrics.items():
                    if key not in self.performance_metrics:
                        self.performance_metrics[key] = []
                    
                    self.performance_metrics[key].append({
                        "timestamp": timestamp,
                        "value": value
                    })
                    
                    # Keep only the last 1000 data points
                    if len(self.performance_metrics[key]) > 1000:
                        self.performance_metrics[key].pop(0)
                
                # Broadcast performance update
                await self._broadcast_event("performance_update", metrics)
                
                # Wait for the next update
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}", exc_info=True)
                await asyncio.sleep(10)  # Wait longer on error
    
    async def startup(self) -> None:
        """Startup tasks."""
        await super().startup()
        
        # Initial refresh of VMs and switches
        await self._refresh_vm_list()
        await self._refresh_switches()
        
        # Start performance monitoring
        self.performance_task = asyncio.create_task(self._monitor_performance())
        
        logger.info("Hyper-V Manager plugin started")
    
    async def shutdown(self) -> None:
        """Shutdown tasks."""
        # Stop performance monitoring
        if hasattr(self, 'performance_task'):
            self.performance_task.cancel()
            try:
                await self.performance_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all background tasks
        for task in list(self.background_tasks.values()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close all WebSocket connections
        for websocket in list(self.websockets):
            try:
                await websocket.close()
            except Exception:
                pass
        
        await super().shutdown()
        logger.info("Hyper-V Manager plugin stopped")



