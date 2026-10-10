"""
Hyper-V Management Tools for virtualization-mcp.

Thin MCP-facing wrappers. All PowerShell work lives in
services/hyperv_manager.py (single source of truth); this module delegates
so the MCP surface and the REST surface can never drift apart again.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _svc():
    from virtualization_mcp.services.hyperv_manager import hyperv_manager as svc

    return svc


async def list_hyperv_vms() -> list[dict[str, Any]]:
    """List all Hyper-V virtual machines."""
    return await _svc().list_vms()


async def get_hyperv_vm(vm_name: str) -> dict[str, Any] | None:
    """Get details of a specific Hyper-V virtual machine."""
    return await _svc().get_vm(vm_name)


async def create_hyperv_vm(
    vm_name: str, memory_mb: int = 2048, disk_gb: int = 25, generation: int = 2
) -> dict[str, Any]:
    """Create a Hyper-V virtual machine."""
    return await _svc().create_vm(vm_name, memory_mb=memory_mb, disk_gb=disk_gb, generation=generation)


async def delete_hyperv_vm(vm_name: str, delete_vhd: bool = True) -> dict[str, Any]:
    """Delete a Hyper-V virtual machine."""
    return await _svc().delete_vm(vm_name, delete_vhd=delete_vhd)


async def start_hyperv_vm(vm_name: str, wait: bool = False) -> dict[str, Any]:
    """Start a Hyper-V virtual machine."""
    del wait  # Hyper-V Start-VM is synchronous enough; kept for API parity
    return await _svc().start_vm(vm_name)


async def stop_hyperv_vm(vm_name: str, force: bool = False, wait: bool = False) -> dict[str, Any]:
    """Stop a Hyper-V virtual machine."""
    del wait
    return await _svc().stop_vm(vm_name, force=force)


async def pause_hyperv_vm(vm_name: str) -> dict[str, Any]:
    """Pause (suspend) a Hyper-V virtual machine."""
    return await _svc().pause_vm(vm_name)


async def resume_hyperv_vm(vm_name: str) -> dict[str, Any]:
    """Resume a paused Hyper-V virtual machine."""
    return await _svc().resume_vm(vm_name)


async def list_hyperv_checkpoints(vm_name: str) -> list[dict[str, Any]]:
    """List checkpoints for a Hyper-V VM."""
    return await _svc().list_checkpoints(vm_name)


async def create_hyperv_checkpoint(vm_name: str, checkpoint_name: str) -> dict[str, Any]:
    """Create a named checkpoint."""
    return await _svc().create_checkpoint(vm_name, checkpoint_name)


async def restore_hyperv_checkpoint(vm_name: str, checkpoint_name: str) -> dict[str, Any]:
    """Restore a named checkpoint."""
    return await _svc().restore_checkpoint(vm_name, checkpoint_name)


async def remove_hyperv_checkpoint(vm_name: str, checkpoint_name: str) -> dict[str, Any]:
    """Delete a named checkpoint."""
    return await _svc().remove_checkpoint(vm_name, checkpoint_name)


async def list_hyperv_switches() -> list[dict[str, Any]]:
    """List Hyper-V virtual switches."""
    return await _svc().list_switches()


async def create_hyperv_switch(switch_name: str, switch_type: str = "Internal") -> dict[str, Any]:
    """Create a Hyper-V virtual switch."""
    return await _svc().create_switch(switch_name, switch_type)


async def connect_hyperv_network(vm_name: str, switch_name: str) -> dict[str, Any]:
    """Connect a VM to a virtual switch."""
    return await _svc().connect_network(vm_name, switch_name)


async def attach_hyperv_iso(vm_name: str, iso_path: str) -> dict[str, Any]:
    """Attach an ISO to a VM DVD drive."""
    return await _svc().attach_iso(vm_name, iso_path)


async def detach_hyperv_iso(vm_name: str) -> dict[str, Any]:
    """Detach ISO from a VM DVD drive."""
    return await _svc().detach_iso(vm_name)


async def get_hyperv_enhanced_session() -> dict[str, Any]:
    """Get host Enhanced Session Mode setting."""
    return await _svc().get_enhanced_session()


async def set_hyperv_enhanced_session(enabled: bool = True) -> dict[str, Any]:
    """Enable/disable host Enhanced Session Mode."""
    return await _svc().set_enhanced_session(enabled)


async def launch_hyperv_console(vm_name: str, server: str = "localhost") -> dict[str, Any]:
    """Launch VMConnect console for a VM (best-effort server-side)."""
    return await _svc().launch_console(vm_name, server)


def hyperv_connect_command(vm_name: str, server: str = "localhost") -> dict[str, Any]:
    """Return the local VMConnect command for a VM."""
    return _svc().connect_command(vm_name, server)


# Backward-compatible model re-exports (moved to plugins.hyperv.manager).
# Kept so `from virtualization_mcp.tools.vm import VirtualMachine, ...` keeps working.
try:
    from virtualization_mcp.plugins.hyperv.manager import (
        VirtualMachine,
        VMDisk,
        VMNetworkAdapter,
        VMSize,
        VMSnapshot,
        VMState,
    )
except Exception:  # pragma: no cover - plugin import should always succeed
    VMDisk = object  # type: ignore[assignment,misc]
    VMNetworkAdapter = object  # type: ignore[assignment,misc]
    VMSize = object  # type: ignore[assignment,misc]
    VMSnapshot = object  # type: ignore[assignment,misc]
    VMState = object  # type: ignore[assignment,misc]
    VirtualMachine = object  # type: ignore[assignment,misc]

__all__ = [
    "VMDisk",
    "VMNetworkAdapter",
    "VMSize",
    "VMSnapshot",
    "VMState",
    "VirtualMachine",
    "attach_hyperv_iso",
    "connect_hyperv_network",
    "create_hyperv_checkpoint",
    "create_hyperv_switch",
    "create_hyperv_vm",
    "delete_hyperv_vm",
    "detach_hyperv_iso",
    "get_hyperv_enhanced_session",
    "get_hyperv_vm",
    "hyperv_connect_command",
    "launch_hyperv_console",
    "list_hyperv_checkpoints",
    "list_hyperv_switches",
    "list_hyperv_vms",
    "pause_hyperv_vm",
    "remove_hyperv_checkpoint",
    "restore_hyperv_checkpoint",
    "resume_hyperv_vm",
    "set_hyperv_enhanced_session",
    "start_hyperv_vm",
    "stop_hyperv_vm",
]
