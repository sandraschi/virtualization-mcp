"""System and Hypervisor Status Router."""

from typing import Any

from fastapi import APIRouter

from virtualization_mcp.tools.portmanteau.system_management import system_management
from virtualization_mcp.utils.resource_guard import ResourceGuard

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Return backend health status and system host metrics."""
    res_status = ResourceGuard.get_system_resource_status()
    sys_info = await system_management(action="host_info")
    return {
        "status": "ok",
        "resource_guard": res_status,
        "system_info": sys_info,
    }
