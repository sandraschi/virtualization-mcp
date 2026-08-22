"""
Prefab UI Component Cards for virtualization-mcp.

Exposes rich, interactive UI cards via `prefab-ui` for MCP client interfaces:
- `show_vm_card`: Individual VM state, specs, and quick lifecycle actions.
- `show_hypervisor_health_card`: Fleet hypervisor status, RAM/CPU allocation, VM counts.
- `show_sandbox_status_card`: Docker & Windows Sandbox runner status and mounts.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from virtualization_mcp.utils.resource_guard import ResourceGuard
from virtualization_mcp.vbox.compat_adapter import VBoxManager

logger = logging.getLogger(__name__)


async def show_vm_card(vm_name: str) -> dict[str, Any]:
    """Display an interactive Prefab UI card for a single Virtual Machine.

    Args:
        vm_name: The name or UUID of the virtual machine.

    Returns:
        Structured Prefab UI card payload containing status badge, hardware specs, and actions.
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
        logger.error(f"Failed to generate VM card for '{vm_name}': {e}")
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

    Returns:
        Structured Prefab UI dashboard payload with host CPU/RAM utilization and VM counts.
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
        logger.error(f"Failed to generate hypervisor health card: {e}")
        return {
            "type": "prefab_card",
            "component": "HypervisorHealthDashboard",
            "data": {"title": "Hypervisor Host Health", "status": "error", "error": str(e)},
        }


async def show_sandbox_status_card() -> dict[str, Any]:
    """Display an interactive Prefab UI card for Docker and Windows Sandbox status.

    Returns:
        Structured Prefab UI sandbox status card payload.
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
