"""
Sandbox Management Portmanteau Tool

Consolidates Docker-based code sandbox operations into a single action-based tool.
Supports ephemeral (fire-and-forget) and stateful (session-based) execution.
Requires Docker Desktop running on the host.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

from virtualization_mcp.tools.sandbox.sandbox_backend import (
    execute_code,
    execute_file,
    session_create,
    session_destroy,
    session_list,
    session_read_file,
    session_run,
    session_write_file,
)
from virtualization_mcp.utils.windows_sandbox_helper import WindowsSandboxHelper

logger = logging.getLogger(__name__)

SANDBOX_ACTIONS = {
    # Ephemeral Docker
    "execute_code": "Run a code snippet in a throwaway container (auto-removed after run)",
    "execute_file": "Run a host file path in a throwaway container (language auto-detected)",
    # Stateful Docker sessions
    "session_create": "Create a persistent sandbox session (container stays alive)",
    "session_run": "Run a shell command in an existing session (state persists)",
    "session_write_file": "Write a file into a running session",
    "session_read_file": "Read a file from a running session",
    "session_list": "List all active sandbox sessions",
    "session_destroy": "Stop and remove a sandbox session",
    # Windows Sandbox bringup & testing
    "win_sandbox_launch_consumer": "Launch nearly-naked Windows Sandbox for install testing (winget bootstrap)",
    "win_sandbox_launch_devinfra": "Launch dev-infra Windows Sandbox (git, python, node, just, biome)",
    "win_sandbox_status": "Check if Windows Sandbox is running and read launch log status",
    "win_sandbox_terminate": "Terminate active singleton Windows Sandbox instance",
}


async def sandbox_management(
    action: Literal[
        "execute_code",
        "execute_file",
        "session_create",
        "session_run",
        "session_write_file",
        "session_read_file",
        "session_list",
        "session_destroy",
        "win_sandbox_launch_consumer",
        "win_sandbox_launch_devinfra",
        "win_sandbox_status",
        "win_sandbox_terminate",
    ],
    code: str | None = None,
    language: Literal["python", "javascript", "bash"] = "python",
    host_path: str | None = None,
    timeout: int = 30,
    network_enabled: bool = False,
    sandbox_id: str | None = None,
    image: str = "python:3.13-slim",
    sandbox_name: str | None = None,
    command: str | None = None,
    container_path: str | None = None,
    content: str | None = None,
    install_claude_desktop: bool = False,
    plain: bool = False,
) -> dict[str, Any]:
    """Docker & Windows Sandbox code execution and bringup tool."""
    try:
        if action not in SANDBOX_ACTIONS:
            return {
                "success": False,
                "error": f"Invalid action '{action}'",
                "available_actions": SANDBOX_ACTIONS,
            }

        logger.info(f"sandbox_management: action={action}")

        # --- Ephemeral ---
        if action == "execute_code":
            if not code:
                return {"success": False, "error": "code is required for execute_code"}
            return execute_code(code=code, language=language, timeout=timeout, network_enabled=network_enabled)

        if action == "execute_file":
            if not host_path:
                return {"success": False, "error": "host_path is required for execute_file"}
            lang = language if language != "python" else None  # allow auto-detect unless explicitly set
            return execute_file(host_path=host_path, language=lang, timeout=timeout, network_enabled=network_enabled)

        # --- Sessions ---
        if action == "session_create":
            return session_create(image=image, name=sandbox_name)

        if action == "session_run":
            if not sandbox_id:
                return {"success": False, "error": "sandbox_id is required for session_run"}
            if not command:
                return {"success": False, "error": "command is required for session_run"}
            return session_run(sandbox_id=sandbox_id, command=command)

        if action == "session_write_file":
            if not sandbox_id:
                return {"success": False, "error": "sandbox_id is required"}
            if not container_path:
                return {"success": False, "error": "container_path is required"}
            if content is None:
                return {"success": False, "error": "content is required"}
            return session_write_file(sandbox_id=sandbox_id, container_path=container_path, content=content)

        if action == "session_read_file":
            if not sandbox_id:
                return {"success": False, "error": "sandbox_id is required"}
            if not container_path:
                return {"success": False, "error": "container_path is required"}
            return session_read_file(sandbox_id=sandbox_id, container_path=container_path)

        if action == "session_list":
            return session_list()

        if action == "session_destroy":
            if not sandbox_id:
                return {"success": False, "error": "sandbox_id is required for session_destroy"}
            return session_destroy(sandbox_id=sandbox_id)

        # --- Windows Sandbox ---
        if action == "win_sandbox_status":
            running = WindowsSandboxHelper.is_sandbox_running()
            return {
                "success": True,
                "action": "win_sandbox_status",
                "running": running,
                "prerequisites": WindowsSandboxHelper().check_prerequisites(),
            }

        if action == "win_sandbox_terminate":
            terminated = WindowsSandboxHelper.terminate_active_sandbox()
            return {
                "success": True,
                "action": "win_sandbox_terminate",
                "terminated": terminated,
                "message": "Terminated active Windows Sandbox process."
                if terminated
                else "No active Windows Sandbox found.",
            }

        if action == "win_sandbox_launch_consumer":
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            ps_script = repo_root / "scripts" / "Launch-ConsumerSandbox.ps1"
            cmd = ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)]
            if install_claude_desktop:
                cmd.append("-InstallClaudeDesktop")
            if plain:
                cmd.append("-Plain")
            subprocess.Popen(cmd)
            return {
                "success": True,
                "action": "win_sandbox_launch_consumer",
                "script": str(ps_script),
                "install_claude_desktop": install_claude_desktop,
                "plain": plain,
                "message": "Launched consumer sandbox script asynchronously.",
            }

        if action == "win_sandbox_launch_devinfra":
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            ps_script = repo_root / "scripts" / "Launch-DevInfraSandbox.ps1"
            cmd = ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)]
            subprocess.Popen(cmd)
            return {
                "success": True,
                "action": "win_sandbox_launch_devinfra",
                "script": str(ps_script),
                "message": "Launched dev-infra sandbox script asynchronously.",
            }

        return {"success": False, "error": f"Action '{action}' not implemented"}

    except Exception as e:
        logger.error(f"sandbox_management error: action={action} error={e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "action": action,
            "hint": "Is Docker Desktop or Windows Sandbox available?",
        }


def register_sandbox_management_tool(mcp: FastMCP) -> None:
    """Register the sandbox management portmanteau tool."""
    mcp.tool(sandbox_management)
