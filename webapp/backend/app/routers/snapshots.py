"""Snapshot management router for webapp backend."""

from typing import Any

from fastapi import APIRouter

from virtualization_mcp.tools.portmanteau.snapshot_management import snapshot_management

router = APIRouter(prefix="/api/snapshots", tags=["Snapshots"])


@router.get("/{vm_name}")
async def list_snapshots(vm_name: str) -> dict[str, Any]:
    """List snapshots for a virtual machine."""
    return await snapshot_management(action="list", vm_name=vm_name)


@router.post("/{vm_name}")
async def create_snapshot(vm_name: str, snapshot_name: str) -> dict[str, Any]:
    """Create a new snapshot."""
    return await snapshot_management(action="create", vm_name=vm_name, snapshot_name=snapshot_name)
