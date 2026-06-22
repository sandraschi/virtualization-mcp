"""Proxmox VE management portmanteau tool.

Provides VM lifecycle operations for Proxmox VE hosts via REST API.
Only active when PROXMOX_HOST env var is configured.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from virtualization_mcp.services.service_manager import service_manager

logger = logging.getLogger(__name__)

PROXMOX_ANNOTATIONS = {"readonly": True}


def register_proxmox_management_tool(mcp: FastMCP) -> None:
    """Register the Proxmox management portmanteau tool.

    Only registers if the Proxmox manager is available (PROXMOX_HOST configured).
    """

    @mcp.tool(
        name="proxmox_management",
        description="""[RATIONALE] Consolidated Proxmox VE management — single tool
for all remote Proxmox operations. Only available when PROXMOX_HOST is configured
in the environment.

Operations:
  - list_vms       List all QEMU VMs on the Proxmox node
  - start_vm       Start a VM by VMID
  - stop_vm        Hard-stop a VM by VMID
  - shutdown_vm    ACPI shutdown a VM by VMID
  - status         Get detailed status for a VM
  - create_snapshot  Create a snapshot
  - list_snapshots   List snapshots for a VM
  - delete_snapshot  Delete a snapshot
  - node_status    Get node CPU/memory/disk usage
  - cluster_resources  List all cluster resources

## Return Format
{"success": bool, "message": str, "data": {...}}

## Examples
  proxmox_management(operation="list_vms")
  proxmox_management(operation="start_vm", vmid="100")
""",
        annotations=PROXMOX_ANNOTATIONS,
    )
    async def proxmox_management(
        operation: str,
        vmid: str | None = None,
        name: str | None = None,
        memory: int = 2048,
        cores: int = 2,
        disk_size: str = "32G",
        iso: str | None = None,
        snapshot_name: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        pm = service_manager.proxmox_manager
        if not pm:
            return {
                "success": False,
                "message": "Proxmox not configured. Set PROXMOX_HOST, PROXMOX_USER, and PROXMOX_PASSWORD env vars.",
                "data": None,
            }

        try:
            if operation == "list_vms":
                vms = pm.list_vms()
                return {"success": True, "message": f"Found {len(vms)} Proxmox VMs", "data": {"vms": vms}}

            elif operation == "start_vm":
                if not vmid:
                    return {"success": False, "message": "vmid required", "data": None}
                result = pm.start_vm(vmid)
                return {"success": True, "message": f"VM {vmid} starting", "data": result}

            elif operation == "stop_vm":
                if not vmid:
                    return {"success": False, "message": "vmid required", "data": None}
                result = pm.stop_vm(vmid)
                return {"success": True, "message": f"VM {vmid} stopping", "data": result}

            elif operation == "shutdown_vm":
                if not vmid:
                    return {"success": False, "message": "vmid required", "data": None}
                result = pm.shutdown_vm(vmid)
                return {"success": True, "message": f"VM {vmid} shutdown initiated", "data": result}

            elif operation == "status":
                if not vmid:
                    return {"success": False, "message": "vmid required", "data": None}
                result = pm.get_vm_status(vmid)
                return {"success": True, "message": f"Status for VM {vmid}", "data": result}

            elif operation == "create_snapshot":
                if not vmid or not snapshot_name:
                    return {"success": False, "message": "vmid and snapshot_name required", "data": None}
                result = pm.create_snapshot(vmid, snapshot_name, description)
                return {"success": True, "message": f"Snapshot {snapshot_name} created", "data": result}

            elif operation == "list_snapshots":
                if not vmid:
                    return {"success": False, "message": "vmid required", "data": None}
                result = pm.list_snapshots(vmid)
                return {"success": True, "message": f"Snapshots for VM {vmid}", "data": {"snapshots": result}}

            elif operation == "delete_snapshot":
                if not vmid or not snapshot_name:
                    return {"success": False, "message": "vmid and snapshot_name required", "data": None}
                result = pm.delete_snapshot(vmid, snapshot_name)
                return {"success": True, "message": f"Snapshot {snapshot_name} deleted", "data": result}

            elif operation == "node_status":
                result = pm.node_status()
                return {"success": True, "message": "Proxmox node status", "data": result}

            elif operation == "cluster_resources":
                result = pm.cluster_resources()
                return {"success": True, "message": "Cluster resources", "data": {"resources": result}}

            else:
                return {"success": False, "message": f"Unknown operation: {operation}", "data": None}

        except Exception as e:
            logger.error("Proxmox operation %s failed: %s", operation, e)
            return {"success": False, "message": f"Proxmox {operation} failed: {e}", "data": None}

    logger.info("Proxmox management tool registered (runtime-configurable)")
