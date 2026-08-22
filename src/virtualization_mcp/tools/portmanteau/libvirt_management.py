"""
Libvirt/KVM Portmanteau Tool

Consolidates QEMU/KVM domain operations into an action-based FastMCP tool.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from virtualization_mcp.plugins.libvirt.manager import LibvirtManager

logger = logging.getLogger(__name__)

LIBVIRT_ACTIONS = ["list", "start", "stop", "status"]


def register_libvirt_management_tool(mcp: FastMCP) -> None:
    """Register libvirt_management portmanteau tool with FastMCP."""

    @mcp.tool()
    async def libvirt_management(
        action: Literal["list", "start", "stop", "status"],
        domain_name: str | None = None,
    ) -> dict[str, Any]:
        """Manage libvirt / QEMU / KVM virtual machine domains.

        Args:
            action: Domain operation ('list', 'start', 'stop', 'status').
            domain_name: Optional domain name or UUID for start/stop/status actions.

        Returns:
            Structured action response dict.
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
