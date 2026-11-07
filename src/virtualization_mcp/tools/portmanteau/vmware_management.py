"""
VMware Workstation Pro Portmanteau Tool (Phase 2).

Consolidates VMware ``vmrun`` operations into an action-based FastMCP tool,
mirroring ``hyperv_management.py``. Phase 2: probe, list/get/start/stop plus
suspend/pause/resume(reset)/unpause, snapshots, clone, guest IP.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from virtualization_mcp.services.vmware_manager import VmwareManager

logger = logging.getLogger(__name__)

VmwareAction = Literal[
    "status",
    "list",
    "get",
    "create",
    "delete",
    "start",
    "stop",
    "reset",
    "suspend",
    "pause",
    "unpause",
    "snapshot_list",
    "snapshot_create",
    "snapshot_revert",
    "snapshot_delete",
    "clone",
    "guest_ip",
]


def register_vmware_management_tool(mcp: FastMCP) -> None:
    """Register the vmware_management portmanteau tool with FastMCP."""

    @mcp.tool()
    async def vmware_management(
        action: Annotated[VmwareAction, Field(description="VMware operation to perform.")] = "status",
        vmx_path: Annotated[str | None, Field(description=".vmx path (all except status/list/create).")] = None,
        gui: Annotated[bool, Field(description="Open Workstation UI on start.")] = False,
        hard: Annotated[bool, Field(description="Hard power-off on stop.")] = False,
        snapshot_name: Annotated[str | None, Field(description="Snapshot name.")] = None,
        dest_vmx: Annotated[str | None, Field(description="Destination .vmx for clone.")] = None,
        full_clone: Annotated[bool, Field(description="Full clone (True) vs linked (False).")] = True,
        name: Annotated[str | None, Field(description="VM display name (create).")] = None,
        memory_mb: Annotated[int, Field(description="RAM in MB (create).")] = 2048,
        cpus: Annotated[int, Field(description="vCPU count (create).")] = 2,
        disk_gb: Annotated[int, Field(description="Disk size in GB (create).")] = 40,
        guest_os: Annotated[
            str | None, Field(description="Guest OS id, e.g. ubuntu-64, windows11-64 (create).")
        ] = None,
        firmware: Annotated[str, Field(description="Firmware: efi or bios (create).")] = "efi",
        iso_path: Annotated[str | None, Field(description="Installer ISO to attach (create).")] = None,
        delete_files: Annotated[bool, Field(description="Remove the VM folder on delete.")] = True,
    ) -> dict[str, Any]:
        """Manage VMware Workstation Pro VMs via vmrun.

        Free since Broadcom Nov 2024. Best Windows option for macOS guests
        (community Unlocker required, Apple-EULA-grey, unsupported here).
        macOS guests crawl on Goliath (no Nvidia Metal driver) - fine for
        slow CLI `xcodebuild` tests, not daily Simulator use.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action`
        performed, and operation data (`vms`, `vm`, `snapshots`, `ip`,
        `available`). Failures carry a human-readable `error`.

        ## Examples

        ```python
        await vmware_management(action="status")
        await vmware_management(action="list")
        await vmware_management(action="start", vmx_path="C:/VMs/macos26/macos26.vmx")
        await vmware_management(action="snapshot_create", vmx_path="C:/VMs/m.vmx", snapshot_name="clean")
        ```
        """
        mgr = VmwareManager()

        if action == "status":
            ok = mgr.is_available()
            return {
                "success": True,
                "action": "status",
                "available": ok,
                "vmrun_path": str(mgr.vmrun_path) if mgr.vmrun_path else None,
                "message": "vmrun found" if ok else "vmrun not found",
            }

        if action == "list":
            try:
                vms = await mgr.list_vms()
                return {"success": True, "action": "list", "count": len(vms), "vms": vms}
            except Exception as e:
                return {"success": False, "action": "list", "error": str(e)}

        needs_vmx = {
            "get",
            "delete",
            "start",
            "stop",
            "reset",
            "suspend",
            "pause",
            "unpause",
            "snapshot_list",
            "snapshot_create",
            "snapshot_revert",
            "snapshot_delete",
            "clone",
            "guest_ip",
        }
        if action in needs_vmx and not vmx_path:
            return {
                "success": False,
                "action": action,
                "error": f"vmx_path is required for action '{action}'",
            }

        try:
            if action == "get":
                vm = await mgr.get_vm(vmx_path or "")
                if vm is None:
                    return {"success": False, "action": "get", "error": f"VM not found: {vmx_path}"}
                return {"success": True, "action": "get", "vm": vm}
            if action == "create":
                if not name or not name.strip():
                    return {"success": False, "action": "create", "error": "name is required for action 'create'"}
                try:
                    result = await mgr.create_vm(
                        name.strip(),
                        memory_mb=memory_mb,
                        cpus=cpus,
                        disk_gb=disk_gb,
                        guest_os=guest_os,
                        firmware=firmware,
                        iso_path=iso_path,
                    )
                except FileExistsError as e:
                    return {"success": False, "action": "create", "error": str(e)}
                return {"success": True, "action": "create", **result}
            if action == "delete":
                result = await mgr.delete_vm(vmx_path or "", delete_files=delete_files)
                return _ok(action, vmx_path, result)
            if action == "start":
                result = await mgr.start_vm(vmx_path or "", gui=gui)
                return _ok(action, vmx_path, result)
            if action == "stop":
                result = await mgr.stop_vm(vmx_path or "", hard=hard)
                return _ok(action, vmx_path, result)
            if action == "reset":
                result = await mgr.reset_vm(vmx_path or "")
                return _ok(action, vmx_path, result)
            if action == "suspend":
                result = await mgr.suspend_vm(vmx_path or "")
                return _ok(action, vmx_path, result)
            if action == "pause":
                result = await mgr.pause_vm(vmx_path or "")
                return _ok(action, vmx_path, result)
            if action == "unpause":
                result = await mgr.unpause_vm(vmx_path or "")
                return _ok(action, vmx_path, result)
            if action == "snapshot_list":
                snaps = await mgr.list_snapshots(vmx_path or "")
                return {"success": True, "action": action, "snapshots": snaps, "count": len(snaps)}
            if action in ("snapshot_create", "snapshot_revert", "snapshot_delete"):
                if not snapshot_name:
                    return {
                        "success": False,
                        "action": action,
                        "error": f"snapshot_name is required for action '{action}'",
                    }
                if action == "snapshot_create":
                    result = await mgr.create_snapshot(vmx_path or "", snapshot_name)
                elif action == "snapshot_revert":
                    result = await mgr.revert_snapshot(vmx_path or "", snapshot_name)
                else:
                    result = await mgr.delete_snapshot(vmx_path or "", snapshot_name)
                return _ok(action, vmx_path, result)
            if action == "clone":
                if not dest_vmx:
                    return {"success": False, "action": action, "error": "dest_vmx is required for clone"}
                result = await mgr.clone_vm(vmx_path or "", dest_vmx, full=full_clone)
                return _ok(action, vmx_path, result)
            if action == "guest_ip":
                result = await mgr.get_guest_ip(vmx_path or "")
                return {"success": True, "action": action, "vmx_path": vmx_path, **result}
        except Exception as e:
            logger.error("vmware_management %s failed: %s", action, e)
            return {"success": False, "action": action, "error": str(e)}

        return {"success": False, "error": f"Unknown action '{action}'"}


def _ok(action: str, vmx_path: str | None, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": result.get("status") == "success",
        "action": action,
        "vmx_path": vmx_path,
        "result": result,
    }
