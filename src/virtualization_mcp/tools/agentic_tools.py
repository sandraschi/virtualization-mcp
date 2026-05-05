"""
Agentic tools for virtualization-mcp — FastMCP 3.2 / SEP-1577.

Sampling-backed operations: VM config suggestion, autonomous workflow,
and the sandbox-for-dangerous-work pattern (spin up → work → tear down).
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


def register_agentic_tools(mcp: FastMCP) -> None:
    """Register agentic tools with FastMCP."""

    @mcp.tool()
    async def vm_agentic_workflow(
        action: Literal["suggest_config", "sandbox_workflow", "workflow"],
        goal: str | None = None,
        use_case: str | None = None,
        vm_name: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """
        Sampling-backed agentic operations for virtualization.

        Actions:
        - suggest_config: Suggest VirtualBox VM settings for a use case via LLM sampling.
          Optional: use_case (e.g. 'CI runner', 'malware sandbox', 'dev environment')
        - sandbox_workflow: Generate a step-by-step plan for the
          spin-up → work → snapshot → tear-down safety pattern.
          Requires: goal (what dangerous/experimental work to do)
        - workflow: Autonomous multi-step VM orchestration goal.
          Requires: goal (natural language objective)

        All actions use ctx.sample() when available; fall back to
        sensible defaults otherwise.
        """
        if action == "suggest_config":
            return await _suggest_config(use_case=use_case, ctx=ctx)
        if action == "sandbox_workflow":
            return await _sandbox_workflow(goal=goal, vm_name=vm_name, ctx=ctx)
        if action == "workflow":
            return await _workflow(goal=goal, ctx=ctx)
        return {"success": False, "error": f"Unknown action: {action}"}


async def _suggest_config(
    use_case: str | None,
    ctx: Context | None,
) -> dict[str, Any]:
    """Suggest VM config for a use case via LLM sampling."""
    if not ctx:
        return {
            "success": True,
            "action": "suggest_config",
            "data": {
                "message": "No sampling context — specify os_type, memory_mb, disk_size_gb manually.",
                "example": {"os_type": "Ubuntu_64", "memory_mb": 2048, "disk_size_gb": 30},
            },
        }
    try:
        prompt = (
            "Suggest a VirtualBox VM configuration (os_type, memory_mb, disk_size_gb) "
            "for the following use case. Reply with a short JSON-like suggestion only — "
            "os_type, memory_mb, disk_size_gb, and one line of reasoning.\n\n"
            f"Use case: {use_case or 'general development'}"
        )
        result = await ctx.sample(
            messages=prompt,
            system_prompt=(
                "You are a virtualization expert. Suggest sensible VM settings. "
                "Use common VirtualBox os_type values: Ubuntu_64, Windows10_64, Debian_64, etc. "
                "memory_mb between 1024 and 8192, disk_size_gb between 20 and 100."
            ),
            temperature=0.3,
            max_tokens=300,
        )
        return {
            "success": True,
            "action": "suggest_config",
            "data": {"suggestion": result.text, "use_case": use_case or "general"},
        }
    except Exception as e:
        return {"success": False, "action": "suggest_config", "error": f"Sampling failed: {e}"}


async def _sandbox_workflow(
    goal: str | None,
    vm_name: str | None,
    ctx: Context | None,
) -> dict[str, Any]:
    """
    Generate a spin-up → work → snapshot → tear-down plan for dangerous/experimental work.
    This is the key pattern for using virtualization-mcp safely.
    """
    if not goal:
        return {"success": False, "action": "sandbox_workflow", "error": "goal is required"}

    if not ctx:
        # Return the generic pattern without LLM customisation
        return {
            "success": True,
            "action": "sandbox_workflow",
            "data": {
                "pattern": "spin-up → snapshot → work → evaluate → restore-or-keep → tear-down",
                "steps": [
                    "vm_management(action='create', ...) or clone an existing base VM",
                    "snapshot_management(action='create', snapshot_name='pre-work-clean')",
                    f"Do the work: {goal}",
                    "Evaluate results",
                    "snapshot_management(action='restore') if something broke, or keep state",
                    "vm_management(action='delete') when done",
                ],
                "goal": goal,
            },
        }

    try:
        prompt = (
            "You are helping plan safe experimental work inside a VirtualBox VM sandbox.\n"
            f"Goal: {goal}\n"
            f"Base VM: {vm_name or 'to be created'}\n\n"
            "Produce a numbered step-by-step plan using these MCP tools:\n"
            "- vm_management (create/start/stop/delete/clone)\n"
            "- snapshot_management (create/restore/delete)\n"
            "- sandbox_management (execute_code/session_* for Docker-based isolation)\n\n"
            "Include: when to snapshot, when to restore, when to tear down. "
            "Be concise — one line per step."
        )
        result = await ctx.sample(messages=prompt, max_tokens=500, temperature=0.2)
        return {
            "success": True,
            "action": "sandbox_workflow",
            "data": {
                "plan": result.text,
                "goal": goal,
                "base_vm": vm_name or "to be created",
                "pattern": "spin-up → snapshot → work → evaluate → restore-or-teardown",
            },
        }
    except Exception as e:
        return {"success": False, "action": "sandbox_workflow", "error": f"Sampling failed: {e}"}


async def _workflow(goal: str | None, ctx: Context | None) -> dict[str, Any]:
    """Autonomous multi-step VM orchestration."""
    if not goal:
        return {"success": False, "action": "workflow", "error": "goal is required"}
    if not ctx:
        return {
            "success": False,
            "action": "workflow",
            "error": "workflow requires a sampling-capable MCP client",
        }
    try:
        prompt = (
            f"Autonomous virtualization task: {goal}\n\n"
            "You have access to: vm_management, snapshot_management, sandbox_management, "
            "network_management, storage_management, system_management, discovery_management.\n"
            "Produce a numbered execution plan. Flag any destructive steps with [DESTRUCTIVE]."
        )
        result = await ctx.sample(messages=prompt, max_tokens=600, temperature=0.2)
        return {
            "success": True,
            "action": "workflow",
            "data": {"plan": result.text, "goal": goal},
        }
    except Exception as e:
        return {"success": False, "action": "workflow", "error": f"Sampling failed: {e}"}
