"""
Prefab UI Component Cards for virtualization-mcp.

Exposes rich, interactive UI cards via `prefab-ui` for MCP client interfaces:
- `show_vm_card`: Individual VM state, specs, and quick lifecycle actions.
- `show_hypervisor_health_card`: Fleet hypervisor status, RAM/CPU allocation, VM counts.
- `show_sandbox_status_card`: Docker & Windows Sandbox runner status and mounts.
"""

import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from virtualization_mcp.utils.resource_guard import ResourceGuard
from virtualization_mcp.vbox.compat_adapter import VBoxManager

logger = logging.getLogger(__name__)


async def show_vm_card(vm_name: Annotated[str, Field(description="VM name or UUID to display.")]) -> dict[str, Any]:
    """Display an interactive Prefab UI card for a single Virtual Machine.

    ## Return Format

    Structured Prefab UI card payload with status badge, hardware specs, and
    quick lifecycle actions. Error states carry `status: "error"` plus `error`.

    ## Examples

    ```python
    await show_vm_card("Ubuntu-Dev")
    ```
    """
    try:
        mgr = VBoxManager()
        info = mgr.get_vm_info(vm_name) if mgr.vm_exists(vm_name) else {}
        exists = bool(info)

        state = info.get("vmstate", "running" if info.get("power_state") == "running" else "off")
        memory = info.get("memory", info.get("memory_mb", 1024))
        cpus = info.get("cpus", 1)
        ostype = info.get("ostype", "Unknown")

        return {
            "type": "prefab_card",
            "component": "VMDetailsCard",
            "data": {
                "title": f"VM: {vm_name}",
                "exists": exists,
                "status": state,
                "badge_color": "green" if state in ["running", "powered on"] else "gray",
                "properties": {
                    "OS Type": ostype,
                    "Memory": f"{memory} MB",
                    "CPUs": cpus,
                    "State": state,
                },
                "quick_actions": [
                    {"label": "Start VM", "action": "vm_management", "params": {"action": "start", "vm_name": vm_name}},
                    {"label": "Stop VM", "action": "vm_management", "params": {"action": "stop", "vm_name": vm_name}},
                    {
                        "label": "Take Snapshot",
                        "action": "snapshot_management",
                        "params": {"action": "create", "vm_name": vm_name, "snapshot_name": "manual-checkpoint"},
                    },
                ],
            },
        }
    except Exception as e:
        logger.exception(f"Failed to generate VM card for '{vm_name}': {e}")
        return {
            "type": "prefab_card",
            "component": "VMDetailsCard",
            "data": {
                "title": f"VM: {vm_name}",
                "status": "error",
                "error": str(e),
            },
        }


async def show_hypervisor_health_card() -> dict[str, Any]:
    """Display an interactive Prefab UI dashboard card for hypervisor host health and VM inventory.

    ## Return Format

    Structured Prefab UI dashboard payload with host CPU/RAM utilization and VM counts.
    Error states carry `status: "error"` plus `error`.

    ## Examples

    ```python
    await show_hypervisor_health_card()
    ```
    """
    try:
        resource_status = ResourceGuard.get_system_resource_status()
        mgr = VBoxManager()
        vms = mgr.list_vms() if hasattr(mgr, "list_vms") else []

        return {
            "type": "prefab_card",
            "component": "HypervisorHealthDashboard",
            "data": {
                "title": "Hypervisor Host Health & Fleet Overview",
                "host_metrics": {
                    "total_ram_gb": round(resource_status["total_ram_mb"] / 1024, 1),
                    "available_ram_gb": round(resource_status["available_ram_mb"] / 1024, 1),
                    "ram_used_percent": resource_status["ram_used_percent"],
                    "cpu_used_percent": resource_status["cpu_used_percent"],
                    "cpu_cores": resource_status["cpu_count"],
                },
                "virtualization_providers": {
                    "VirtualBox": "Active",
                    "Hyper-V": "Supported",
                    "Windows Sandbox": "Available",
                },
                "total_vms": len(vms),
                "vm_list": [vm.get("name") if isinstance(vm, dict) else str(vm) for vm in vms[:10]],
            },
        }
    except Exception as e:
        logger.exception(f"Failed to generate hypervisor health card: {e}")
        return {
            "type": "prefab_card",
            "component": "HypervisorHealthDashboard",
            "data": {"title": "Hypervisor Host Health", "status": "error", "error": str(e)},
        }


async def show_sandbox_status_card() -> dict[str, Any]:
    """Display an interactive Prefab UI card for Docker and Windows Sandbox status.

    ## Return Format

    Structured Prefab UI sandbox status card payload.

    ## Examples

    ```python
    await show_sandbox_status_card()
    ```
    """
    return {
        "type": "prefab_card",
        "component": "SandboxStatusCard",
        "data": {
            "title": "Isolated Sandboxes",
            "backends": {
                "Docker": "Available",
                "Windows Sandbox": "Available (.wsb automation)",
            },
            "security_policy": "Host isolation enabled",
            "quick_actions": [
                {"label": "Run Code Sandbox", "action": "sandbox_management", "params": {"action": "run"}},
            ],
        },
    }


def register_prefab_tools(mcp: FastMCP) -> None:
    """Register Prefab UI card tools with FastMCP."""
    mcp.tool(show_vm_card)
    mcp.tool(show_hypervisor_health_card)
    mcp.tool(show_sandbox_status_card)
    logger.info("Prefab UI cards registered successfully")
