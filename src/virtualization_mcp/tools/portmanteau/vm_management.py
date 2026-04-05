"""
VM Management Portmanteau Tool

Consolidates all VM-related operations into a single tool with action-based interface.
Replaces 11 individual VM tools with one comprehensive tool.
FastMCP 3.1: optional Context for progress reporting and agentic workflows.
"""

import logging
from typing import Any, Literal

from fastmcp import Context, FastMCP

from virtualization_mcp.schemas.vbox_types import VBoxGuestOSType
from virtualization_mcp.tools.vm.vm_tools import (
    clone_vm,
    create_vm,
    delete_vm,
    get_vm_info,
    list_vms,
    pause_vm,
    reset_vm,
    resume_vm,
    start_vm,
    stop_vm,
)

logger = logging.getLogger(__name__)

# Define available actions (suggest_config uses LLM sampling when ctx available)
VM_ACTIONS = {
    "list": "List all virtual machines",
    "create": "Create a new virtual machine",
    "start": "Start a virtual machine",
    "stop": "Stop a running virtual machine",
    "delete": "Delete a virtual machine",
    "clone": "Clone a virtual machine",
    "reset": "Reset a virtual machine",
    "pause": "Pause a virtual machine",
    "resume": "Resume a paused virtual machine",
    "info": "Get detailed information about a virtual machine",
    "suggest_config": "Suggest VM configuration using LLM (FastMCP 3.1 sampling)",
}


def register_vm_management_tool(mcp: FastMCP) -> None:
    """Register the VM management portmanteau tool."""

    @mcp.tool()
    async def vm_management(
        action: Literal[
            "list",
            "create",
            "start",
            "stop",
            "delete",
            "clone",
            "reset",
            "pause",
            "resume",
            "info",
            "suggest_config",
        ],
        vm_name: str | None = None,
        source_vm: str | None = None,
        new_vm_name: str | None = None,
        os_type: VBoxGuestOSType | None = None,
        memory_mb: int | None = None,
        disk_size_gb: int | None = None,
        use_case: str | None = None,
        limit: int = 100,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive virtual machine management portmanteau tool.

        This tool consolidates all VM operations into a single interface. Use the 'action' parameter
        to specify which operation to perform. Different actions require different parameters.

        Args:
            action (required): The operation to perform. Must be one of:
                - "list": List all virtual machines (no other parameters required)
                - "create": Create a new virtual machine (requires: vm_name, os_type, memory_mb, disk_size_gb)
                - "start": Start a virtual machine (requires: vm_name)
                - "stop": Stop a running virtual machine (requires: vm_name)
                - "delete": Delete a virtual machine (requires: vm_name)
                - "clone": Clone an existing virtual machine (requires: source_vm, new_vm_name)
                - "reset": Reset a virtual machine (requires: vm_name)
                - "pause": Pause a running virtual machine (requires: vm_name)
                - "resume": Resume a paused virtual machine (requires: vm_name)
                - "info": Get detailed information about a virtual machine (requires: vm_name)
            - "suggest_config": Suggest VM configuration for a use case (optional: use_case). Uses LLM when available (FastMCP 3.1).

            vm_name: Registered VM name or UUID (VBoxManage name). Required for most actions except list/suggest_config.
            use_case: Short description for suggest_config (e.g. "development", "gaming", "CI runner")
            source_vm: Source VM name or UUID for clone (required for "clone"); must exist on host.
            new_vm_name: New unique VM name for clone (required for "clone").
            os_type: VirtualBox guest OS id for create (VBoxManage --ostype). Use system_management(action="ostypes") for the full list.
            memory_mb: RAM for create (128–host max MB; typical 1024–65536)
            disk_size_gb: Primary disk size for create (>=1 GB)
            limit: For action=list only: max VMs per page (1–500, default 100)
            offset: For action=list only: skip N VMs before returning a page

        Returns:
            success (bool), action (str), and one of:
            - list: data (dict from list_vms: total, count, vms[], has_more, limit, offset), count (page size)
            - create/start/stop/...: data (underlying tool dict with status/message/vm_info/…)
            - On failure: error (str), recovery_options (list[str]) when applicable

        Examples:
            # List all VMs - simplest usage, no other parameters needed
            result = await vm_management(action="list")

            # Create a new VM - requires vm_name, os_type, memory_mb, disk_size_gb
            result = await vm_management(
                action="create",
                vm_name="MyVM",
                os_type="Windows10_64",
                memory_mb=4096,
                disk_size_gb=50
            )

            # Start a VM - requires vm_name
            result = await vm_management(action="start", vm_name="MyVM")

            # Get VM information - requires vm_name
            result = await vm_management(action="info", vm_name="MyVM")

            # Clone a VM - requires source_vm and new_vm_name
            result = await vm_management(
                action="clone",
                source_vm="MyVM",
                new_vm_name="MyVM_Clone"
            )
        """
        try:
            # Validate action
            if action not in VM_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(VM_ACTIONS.keys())}",
                    "available_actions": VM_ACTIONS,
                }

            logger.info("Executing VM management action: %s", action)

            if action == "suggest_config":
                return await _handle_suggest_config(use_case=use_case, ctx=ctx)

            if ctx:
                try:
                    await ctx.report_progress(progress=0, total=100)
                except Exception:
                    pass

            # Route to appropriate function based on action
            if action == "list":
                return await _handle_list_vms(ctx=ctx, limit=limit, offset=offset)

            elif action == "create":
                return await _handle_create_vm(
                    vm_name=vm_name,
                    os_type=os_type,
                    memory_mb=memory_mb,
                    disk_size_gb=disk_size_gb,
                    ctx=ctx,
                )

            elif action == "start":
                return await _handle_start_vm(vm_name=vm_name)

            elif action == "stop":
                return await _handle_stop_vm(vm_name=vm_name)

            elif action == "delete":
                return await _handle_delete_vm(vm_name=vm_name)

            elif action == "clone":
                return await _handle_clone_vm(source_vm=source_vm, new_vm_name=new_vm_name, ctx=ctx)

            elif action == "reset":
                return await _handle_reset_vm(vm_name=vm_name)

            elif action == "pause":
                return await _handle_pause_vm(vm_name=vm_name)

            elif action == "resume":
                return await _handle_resume_vm(vm_name=vm_name)

            elif action == "info":
                return await _handle_get_vm_info(vm_name=vm_name)

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": VM_ACTIONS,
                }

        except Exception as e:
            logger.error(f"Error in VM management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "available_actions": VM_ACTIONS,
            }


async def _handle_list_vms(
    ctx: Context | None = None, limit: int = 100, offset: int = 0
) -> dict[str, Any]:
    """Handle list VMs action."""
    try:
        if ctx:
            try:
                await ctx.report_progress(progress=10, total=100)
            except Exception:
                pass
        result = await list_vms(details=True, limit=limit, offset=offset)
        if ctx:
            try:
                await ctx.report_progress(progress=100, total=100)
            except Exception:
                pass
        count = result.get("count", 0) if isinstance(result, dict) else 0
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "list",
            "data": result,
            "count": count,
            "total": result.get("total") if isinstance(result, dict) else None,
            "has_more": result.get("has_more") if isinstance(result, dict) else None,
            "recovery_options": result.get("recovery_options") if isinstance(result, dict) else None,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list",
            "error": f"Failed to list VMs: {str(e)}",
            "recovery_options": ["Verify VBoxManage works on the host", "Retry with a smaller limit"],
        }


async def _handle_suggest_config(
    use_case: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Suggest VM configuration using LLM sampling (FastMCP 3.1). When ctx is available, uses ctx.sample()."""
    if not ctx:
        return {
            "success": True,
            "action": "suggest_config",
            "data": {
                "message": "LLM sampling not available in this context. Use MCP client with sampling support, or specify os_type, memory_mb, disk_size_gb manually.",
                "example": {"os_type": "Ubuntu_64", "memory_mb": 2048, "disk_size_gb": 30},
            },
        }
    try:
        prompt = (
            "Suggest a VirtualBox VM configuration (os_type, memory_mb, disk_size_gb) "
            "for the following use case. Reply with a short JSON-like suggestion only, "
            "e.g. os_type, memory_mb, disk_size_gb, and one line of reasoning."
        )
        if use_case:
            prompt += f"\n\nUse case: {use_case}"
        else:
            prompt += "\n\nUse case: general development."
        result = await ctx.sample(
            messages=prompt,
            system_prompt=(
                "You are a virtualization expert. Suggest sensible VM settings. "
                "Use common os_type values: Ubuntu_64, Windows10_64, Debian_64, etc. "
                "Keep memory_mb between 1024 and 8192, disk_size_gb between 20 and 100."
            ),
            temperature=0.3,
            max_tokens=400,
        )
        text = result.text or ""
        return {
            "success": True,
            "action": "suggest_config",
            "data": {"suggestion": text, "use_case": use_case or "general"},
        }
    except Exception as e:
        logger.exception("suggest_config sampling failed")
        return {
            "success": False,
            "action": "suggest_config",
            "error": f"LLM suggestion failed: {e}",
        }


async def _handle_create_vm(
    vm_name: str | None = None,
    os_type: str | None = None,
    memory_mb: int | None = None,
    disk_size_gb: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Handle create VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "create",
            "error": "vm_name is required for create action",
        }

    if not os_type:
        return {
            "success": False,
            "action": "create",
            "error": "os_type is required for create action",
        }

    try:
        if ctx:
            try:
                await ctx.report_progress(progress=20, total=100)
            except Exception:
                pass
        result = await create_vm(
            name=vm_name,
            ostype=os_type,
            memory_mb=memory_mb or 1024,
            disk_size_gb=disk_size_gb or 20,
        )
        if ctx:
            try:
                await ctx.report_progress(progress=100, total=100)
            except Exception:
                pass
        ok = isinstance(result, dict) and result.get("status") == "success"
        out: dict[str, Any] = {
            "success": ok,
            "action": "create",
            "vm_name": vm_name,
            "data": result,
        }
        if not ok and isinstance(result, dict):
            out["recovery_options"] = [
                "Run system_management(action=\"ostypes\") and pick a valid os_type",
                "Ensure vm_name is unique (list_vms)",
            ]
        return out
    except Exception as e:
        return {
            "success": False,
            "action": "create",
            "vm_name": vm_name,
            "error": f"Failed to create VM: {str(e)}",
            "recovery_options": ["Check VBoxManage stderr in logs", "Validate disk path and free space"],
        }


async def _handle_start_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle start VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "start",
            "error": "vm_name is required for start action",
        }

    try:
        result = await start_vm(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        return {
            "success": ok,
            "action": "start",
            "vm_name": vm_name,
            "data": result,
            "recovery_options": None
            if ok
            else (result.get("recovery_options") if isinstance(result, dict) else None),
        }
    except Exception as e:
        return {
            "success": False,
            "action": "start",
            "vm_name": vm_name,
            "error": f"Failed to start VM: {str(e)}",
            "recovery_options": ["Verify the VM exists (list_vms)", "Check that another VM does not hold locks"],
        }


async def _handle_stop_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle stop VM action."""
    if not vm_name:
        return {"success": False, "action": "stop", "error": "vm_name is required for stop action"}

    try:
        result = await stop_vm(vm_name=vm_name)
        return {"success": True, "action": "stop", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "stop",
            "vm_name": vm_name,
            "error": f"Failed to stop VM: {str(e)}",
        }


async def _handle_delete_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle delete VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "delete",
            "error": "vm_name is required for delete action",
        }

    try:
        result = await delete_vm(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        out: dict[str, Any] = {
            "success": ok,
            "action": "delete",
            "vm_name": vm_name,
            "data": result,
        }
        if not ok and isinstance(result, dict) and result.get("recovery_options"):
            out["recovery_options"] = result["recovery_options"]
        return out
    except Exception as e:
        return {
            "success": False,
            "action": "delete",
            "vm_name": vm_name,
            "error": f"Failed to delete VM: {str(e)}",
            "recovery_options": ["Power off the VM and retry", "Verify name/UUID with list_vms"],
        }


async def _handle_clone_vm(
    source_vm: str | None = None,
    new_vm_name: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Handle clone VM action."""
    if not source_vm:
        return {
            "success": False,
            "action": "clone",
            "error": "source_vm is required for clone action",
        }

    if not new_vm_name:
        return {
            "success": False,
            "action": "clone",
            "error": "new_vm_name is required for clone action",
        }

    try:
        if ctx:
            try:
                await ctx.report_progress(progress=25, total=100)
            except Exception:
                pass
        result = await clone_vm(source_vm=source_vm, new_name=new_vm_name)
        if ctx:
            try:
                await ctx.report_progress(progress=100, total=100)
            except Exception:
                pass
        ok = isinstance(result, dict) and result.get("status") == "success"
        out: dict[str, Any] = {
            "success": ok,
            "action": "clone",
            "source_vm": source_vm,
            "new_vm_name": new_vm_name,
            "data": result,
        }
        if not ok and isinstance(result, dict) and result.get("recovery_options"):
            out["recovery_options"] = result["recovery_options"]
        return out
    except Exception as e:
        return {
            "success": False,
            "action": "clone",
            "source_vm": source_vm,
            "new_vm_name": new_vm_name,
            "error": f"Failed to clone VM: {str(e)}",
            "recovery_options": ["Confirm source_vm exists", "Use a unique new_vm_name"],
        }


async def _handle_reset_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle reset VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "reset",
            "error": "vm_name is required for reset action",
        }

    try:
        result = await reset_vm(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        return {
            "success": ok,
            "action": "reset",
            "vm_name": vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "reset",
            "vm_name": vm_name,
            "error": f"Failed to reset VM: {str(e)}",
        }


async def _handle_pause_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle pause VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "pause",
            "error": "vm_name is required for pause action",
        }

    try:
        result = await pause_vm(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        return {"success": ok, "action": "pause", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "pause",
            "vm_name": vm_name,
            "error": f"Failed to pause VM: {str(e)}",
        }


async def _handle_resume_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle resume VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "resume",
            "error": "vm_name is required for resume action",
        }

    try:
        result = await resume_vm(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        return {"success": ok, "action": "resume", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "resume",
            "vm_name": vm_name,
            "error": f"Failed to resume VM: {str(e)}",
        }


async def _handle_get_vm_info(vm_name: str | None = None) -> dict[str, Any]:
    """Handle get VM info action."""
    if not vm_name:
        return {"success": False, "action": "info", "error": "vm_name is required for info action"}

    try:
        result = await get_vm_info(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        out: dict[str, Any] = {
            "success": ok,
            "action": "info",
            "vm_name": vm_name,
            "data": result,
        }
        if not ok and isinstance(result, dict) and result.get("recovery_options"):
            out["recovery_options"] = result["recovery_options"]
        return out
    except Exception as e:
        return {
            "success": False,
            "action": "info",
            "vm_name": vm_name,
            "error": f"Failed to get VM info: {str(e)}",
        }
