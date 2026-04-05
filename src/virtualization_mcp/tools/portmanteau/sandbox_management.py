"""
Sandbox Management Portmanteau Tool

Consolidates Docker-based code sandbox operations into a single action-based tool.
Supports ephemeral (fire-and-forget) and stateful (session-based) execution.
Requires Docker Desktop running on the host.
"""

import logging
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

logger = logging.getLogger(__name__)

SANDBOX_ACTIONS = {
    # Ephemeral
    "execute_code": "Run a code snippet in a throwaway container (auto-removed after run)",
    "execute_file": "Run a host file path in a throwaway container (language auto-detected)",
    # Stateful sessions
    "session_create": "Create a persistent sandbox session (container stays alive)",
    "session_run": "Run a shell command in an existing session (state persists)",
    "session_write_file": "Write a file into a running session",
    "session_read_file": "Read a file from a running session",
    "session_list": "List all active sandbox sessions",
    "session_destroy": "Stop and remove a sandbox session",
}


def register_sandbox_management_tool(mcp: FastMCP) -> None:
    """Register the sandbox management portmanteau tool."""

    @mcp.tool()
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
    ) -> dict[str, Any]:
        """
        Docker-based code sandbox management for safe, isolated code execution.

        Requires Docker Desktop running on the host. Two execution modes:
        - Ephemeral: throwaway container, auto-removed after run (execute_code, execute_file)
        - Stateful: persistent session, state preserved between calls (session_*)

        Args:
            action (required): Operation to perform. One of:
                --- EPHEMERAL (throwaway containers) ---
                - "execute_code": Run code snippet. Requires: code. Optional: language, timeout, network_enabled
                - "execute_file": Run a host file. Requires: host_path. Optional: language, timeout, network_enabled

                --- STATEFUL SESSIONS (persistent containers) ---
                - "session_create": Create session. Optional: image, sandbox_name
                - "session_run": Run command in session. Requires: sandbox_id, command
                - "session_write_file": Write file to session. Requires: sandbox_id, container_path, content
                - "session_read_file": Read file from session. Requires: sandbox_id, container_path
                - "session_list": List active sessions. No extra args needed.
                - "session_destroy": Remove session. Requires: sandbox_id

            code: Code string to execute (for execute_code)
            language: "python" | "javascript" | "bash" (default: python)
            host_path: Absolute Windows path to file (for execute_file)
            timeout: Max execution seconds (default: 30)
            network_enabled: Allow outbound network in container (default: False)
            sandbox_id: Session ID from session_create (for session_* actions)
            image: Docker image for session_create (default: python:3.13-slim)
            sandbox_name: Optional container name for session_create
            command: Shell command for session_run
            container_path: Path inside container for file operations
            content: File content string for session_write_file

        Returns:
            Dict with: success, action, output/content/sessions (action-specific), error (if failed)

        Examples:
            # Run a Python snippet
            sandbox_management(action="execute_code", code="print(2+2)", language="python")

            # Run a file
            sandbox_management(action="execute_file", host_path="D:/Dev/repos/myapp/test.py")

            # Multi-step session: install package then run code
            r = sandbox_management(action="session_create", image="python:3.13-slim")
            sid = r["sandbox_id"]
            sandbox_management(action="session_run", sandbox_id=sid, command="pip install requests -q")
            sandbox_management(action="session_run", sandbox_id=sid, command="python -c 'import requests; print(requests.__version__)'")
            sandbox_management(action="session_destroy", sandbox_id=sid)
        """
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

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"sandbox_management error: action={action} error={e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "hint": "Is Docker Desktop running? Check with: docker ps",
            }
