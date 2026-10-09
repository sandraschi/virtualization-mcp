"""
Libvirt/KVM Portmanteau Tool

Consolidates QEMU/KVM domain operations into an action-based FastMCP tool.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from virtualization_mcp.plugins.libvirt.manager import LibvirtManager

logger = logging.getLogger(__name__)

LIBVIRT_ACTIONS = ["list", "start", "stop", "status"]


def register_libvirt_management_tool(mcp: FastMCP) -> None:
    """Register libvirt_management portmanteau tool with FastMCP."""

    @mcp.tool()
    async def libvirt_management(
        action: Annotated[
            Literal["list", "start", "stop", "status"], Field(description="Domain operation to perform.")
        ],
        domain_name: Annotated[str | None, Field(description="Domain name or UUID (start, stop, status).")] = None,
    ) -> dict[str, Any]:
        """Manage libvirt / QEMU / KVM virtual machine domains.

        Native Linux and WSL2 hypervisor backend via `virsh`.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        and operation data (`domains`, `result`, `available`). Failures carry a
        human-readable `error`.

        ## Examples

        ```python
        await libvirt_management(action="list")
        await libvirt_management(action="status")
        await libvirt_management(action="start", domain_name="my-vm")
        await libvirt_management(action="stop", domain_name="my-vm")
        ```
        """
        mgr = LibvirtManager()

        if action == "status":
            return {
                "success": True,
                "action": "status",
                "available": mgr.is_available(),
                "virsh_path": mgr.virsh_path,
            }

        if action == "list":
            domains = mgr.list_domains()
            return {
                "success": True,
                "action": "list",
                "count": len(domains),
                "domains": domains,
            }

        if action in ["start", "stop"]:
            if not domain_name:
                return {
                    "success": False,
                    "action": action,
                    "error": f"domain_name is required for action '{action}'",
                }
            result = mgr.start_domain(domain_name) if action == "start" else mgr.stop_domain(domain_name)
            return {
                "success": result.get("status") == "success",
                "action": action,
                "domain_name": domain_name,
                "result": result,
            }

        return {"success": False, "error": f"Unknown action '{action}'"}
