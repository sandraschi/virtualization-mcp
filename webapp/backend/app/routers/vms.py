"""VM operations router for webapp backend."""

from typing import Any

from fastapi import APIRouter, HTTPException

from virtualization_mcp.tools.portmanteau.vm_management import vm_management

router = APIRouter(prefix="/api/vms", tags=["VMs"])


@router.get("/")
async def list_vms() -> dict[str, Any]:
    """List all registered virtual machines."""
    return await vm_management(action="list")


@router.get("/{vm_name}")
async def get_vm_details(vm_name: str) -> dict[str, Any]:
    """Get VM information details."""
    res = await vm_management(action="info", vm_name=vm_name)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found")
    return res


@router.post("/{vm_name}/start")
async def start_vm(vm_name: str) -> dict[str, Any]:
    """Start a virtual machine."""
    return await vm_management(action="start", vm_name=vm_name)


@router.post("/{vm_name}/stop")
async def stop_vm(vm_name: str) -> dict[str, Any]:
    """Stop a virtual machine."""
    return await vm_management(action="stop", vm_name=vm_name)
