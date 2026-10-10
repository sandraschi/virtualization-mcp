"""
Hyper-V Management Portmanteau Tool

Consolidates all Hyper-V related operations into a single tool.
Provides Windows Hyper-V VM management capabilities, including VMConnect
console, checkpoints, VMSwitch networking, and ISO media.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# Define available actions
HYPERV_ACTIONS = {
    "list": "List all Hyper-V virtual machines",
    "get": "Get detailed information about a Hyper-V VM",
    "create": "Create a Hyper-V virtual machine",
    "delete": "Delete a Hyper-V virtual machine",
    "start": "Start a Hyper-V virtual machine",
    "stop": "Stop a Hyper-V virtual machine",
    "pause": "Pause (suspend) a Hyper-V virtual machine",
    "resume": "Resume a paused Hyper-V virtual machine",
    "checkpoint_list": "List checkpoints for a Hyper-V VM",
    "checkpoint_create": "Create a named checkpoint",
    "checkpoint_restore": "Restore a named checkpoint",
    "checkpoint_delete": "Delete a named checkpoint",
    "switch_list": "List Hyper-V virtual switches",
    "switch_create": "Create a Hyper-V virtual switch",
    "network_connect": "Connect a VM to a virtual switch",
    "iso_attach": "Attach an ISO to a VM DVD drive",
    "iso_detach": "Detach ISO from a VM DVD drive",
    "enhanced_get": "Get host Enhanced Session Mode setting",
    "enhanced_set": "Enable/disable host Enhanced Session Mode",
    "console": "Launch VMConnect console (best-effort) / get local command",
}

HyperVAction = Literal[
    "list",
    "get",
    "create",
    "delete",
    "start",
    "stop",
    "pause",
    "resume",
    "checkpoint_list",
    "checkpoint_create",
    "checkpoint_restore",
    "checkpoint_delete",
    "switch_list",
    "switch_create",
    "network_connect",
    "iso_attach",
    "iso_detach",
    "enhanced_get",
    "enhanced_set",
    "console",
]


def register_hyperv_management_tool(mcp: FastMCP) -> None:
    """Register the Hyper-V management portmanteau tool."""

    @mcp.tool()
    async def hyperv_management(
        action: Annotated[HyperVAction, Field(description="Hyper-V operation to perform.")],
        vm_name: Annotated[str | None, Field(description="Hyper-V VM name.")] = None,
        checkpoint_name: Annotated[str | None, Field(description="Checkpoint name.")] = None,
        switch_name: Annotated[str | None, Field(description="Virtual switch name.")] = None,
        switch_type: Annotated[str, Field(description="Switch type: External, Internal, Private.")] = "Internal",
        iso_path: Annotated[str | None, Field(description="ISO path for iso_attach.")] = None,
        memory_mb: Annotated[int, Field(description="RAM in MB for create.")] = 2048,
        disk_gb: Annotated[int, Field(description="Disk in GB for create.")] = 25,
        generation: Annotated[int, Field(description="VM generation 1 or 2 for create.")] = 2,
        enabled: Annotated[bool, Field(description="Enabled flag for enhanced_set.")] = True,
        server: Annotated[str, Field(description="Hyper-V host for console.")] = "localhost",
        force: Annotated[bool, Field(description="Force stop without graceful shutdown (stop only).")] = False,
        delete_vhd: Annotated[bool, Field(description="Remove VHD folder on delete.")] = True,
        wait: Annotated[bool, Field(description="Wait for completion (start, stop).")] = False,
    ) -> dict[str, Any]:
        """Comprehensive Hyper-V management portmanteau tool (Windows only).

        Consolidates all Hyper-V virtual machine operations into a single interface.
        Only works on Windows systems with Hyper-V enabled.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        `vm_name`, and operation data (`vms`, `vm_info`, `result`). Failures carry
        a human-readable `error`.

        ## Examples

        ```python
        await hyperv_management(action="list")
        await hyperv_management(action="get", vm_name="MyHyperVVM")
        await hyperv_management(action="start", vm_name="MyHyperVVM", wait=True)
        await hyperv_management(action="stop", vm_name="MyHyperVVM", force=True)
        await hyperv_management(action="checkpoint_create", vm_name="VM", checkpoint_name="pre-patch")
        await hyperv_management(action="console", vm_name="VM")
        ```
        """
        try:
            if action not in HYPERV_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(HYPERV_ACTIONS.keys())}",
                    "available_actions": HYPERV_ACTIONS,
                }

            logger.info(f"Executing Hyper-V management action: {action}")

            from virtualization_mcp.tools.vm import hyperv_tools as hv

            if action == "list":
                vms = await hv.list_hyperv_vms()
                return {"success": True, "action": action, "vms": vms, "count": len(vms)}

            if action == "switch_list":
                switches = await hv.list_hyperv_switches()
                return {"success": True, "action": action, "switches": switches}

            if action == "enhanced_get":
                result = await hv.get_hyperv_enhanced_session()
                return {"success": True, "action": action, "result": result}

            if action == "enhanced_set":
                result = await hv.set_hyperv_enhanced_session(enabled)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "result": result}

            if action == "console" and vm_name:
                result = await hv.launch_hyperv_console(vm_name, server)
                return {"success": True, "action": action, "vm_name": vm_name, "result": result}

            if action == "create" and vm_name:
                result = await hv.create_hyperv_vm(vm_name, memory_mb, disk_gb, generation)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "delete" and vm_name:
                result = await hv.delete_hyperv_vm(vm_name, delete_vhd)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "get" and vm_name:
                vm_info = await hv.get_hyperv_vm(vm_name)
                if vm_info is None:
                    return {"success": False, "error": f"Hyper-V VM '{vm_name}' not found", "vm_name": vm_name}
                return {"success": True, "action": action, "vm_name": vm_name, "vm_info": vm_info}

            if action == "start" and vm_name:
                result = await hv.start_hyperv_vm(vm_name, wait=wait)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "stop" and vm_name:
                result = await hv.stop_hyperv_vm(vm_name, force=force, wait=wait)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "force": force, "result": result}

            if action == "pause" and vm_name:
                result = await hv.pause_hyperv_vm(vm_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "resume" and vm_name:
                result = await hv.resume_hyperv_vm(vm_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "checkpoint_list" and vm_name:
                cps = await hv.list_hyperv_checkpoints(vm_name)
                return {"success": True, "action": action, "vm_name": vm_name, "checkpoints": cps}

            if action == "checkpoint_create" and vm_name and checkpoint_name:
                result = await hv.create_hyperv_checkpoint(vm_name, checkpoint_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "checkpoint_restore" and vm_name and checkpoint_name:
                result = await hv.restore_hyperv_checkpoint(vm_name, checkpoint_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "checkpoint_delete" and vm_name and checkpoint_name:
                result = await hv.remove_hyperv_checkpoint(vm_name, checkpoint_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "switch_create" and switch_name:
                result = await hv.create_hyperv_switch(switch_name, switch_type)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "result": result}

            if action == "network_connect" and vm_name and switch_name:
                result = await hv.connect_hyperv_network(vm_name, switch_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "iso_attach" and vm_name and iso_path:
                result = await hv.attach_hyperv_iso(vm_name, iso_path)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            if action == "iso_detach" and vm_name:
                result = await hv.detach_hyperv_iso(vm_name)
                ok = result.get("status") == "success"
                return {"success": ok, "action": action, "vm_name": vm_name, "result": result}

            return {
                "success": False,
                "error": f"Action '{action}' missing required parameters (vm_name/checkpoint_name/switch_name/iso_path).",
                "action": action,
            }

        except Exception as e:
            logger.error(f"Hyper-V management error for action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Hyper-V operation failed: {e!s}",
                "action": action,
            }
