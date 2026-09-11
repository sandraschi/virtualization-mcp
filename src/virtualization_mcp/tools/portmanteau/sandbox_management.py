"""
Sandbox Management Portmanteau Tool

Consolidates Docker-based code sandbox operations into a single action-based tool.
Supports ephemeral (fire-and-forget) and stateful (session-based) execution.
Requires Docker Desktop running on the host.
"""

import logging
import subprocess
from datetime import UTC
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
    "win_sandbox_naked_test": "Launch automated naked install test in Windows Sandbox (repo in, RESULT.json out)",
    "win_sandbox_naked_test_status": "Poll or retrieve RESULT.json from a naked install test job",
    "win_sandbox_naked_test_list": "List recent naked install test jobs with pass/fail summary",
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
        "win_sandbox_naked_test",
        "win_sandbox_naked_test_status",
        "win_sandbox_naked_test_list",
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
    repo: str | None = None,
    branch: str = "main",
    observe_sec: int = 90,
    health_url: str | None = None,
    job_id: str | None = None,
    memory_in_mb: int = 8192,
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

        if action == "win_sandbox_naked_test":
            if not repo:
                return {"success": False, "error": "repo is required (owner/name or https URL)"}
            repo_clean = repo.strip()
            if repo_clean.startswith("http"):
                repo_url = repo_clean
            elif "/" in repo_clean and " " not in repo_clean:
                repo_url = f"https://github.com/{repo_clean}.git"
            else:
                return {"success": False, "error": "repo must be owner/name or an https URL"}

            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            assets_folder = repo_root / "assets" / "sandbox"
            if not assets_folder.is_dir():
                return {"success": False, "error": f"Sandbox assets missing: {assets_folder}"}

            runs_root = repo_root.parent / "_sandbox_runs"
            runs_root.mkdir(parents=True, exist_ok=True)

            import json
            import tempfile
            import xml.sax.saxutils as sax
            from datetime import datetime

            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            safe_repo = "".join(
                c if c.isalnum() or c in "-_" else "-" for c in repo_url.split("/")[-1].replace(".git", "")
            )
            jid = f"naked-{safe_repo}-{stamp}"
            job_dir = runs_root / jid
            job_dir.mkdir(parents=True, exist_ok=True)

            spec_path = job_dir / "spec.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "repo_url": repo_url,
                        "branch": branch or "main",
                        "observe_sec": observe_sec or 90,
                        "health_url": health_url or "",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            assets_escaped = sax.escape(str(assets_folder))
            job_escaped = sax.escape(str(job_dir))
            wsb_xml = f"""<Configuration>
<MappedFolders>
<MappedFolder>
<HostFolder>{assets_escaped}</HostFolder>
<SandboxFolder>C:\\Assets</SandboxFolder>
<ReadOnly>false</ReadOnly>
</MappedFolder>
<MappedFolder>
<HostFolder>{job_escaped}</HostFolder>
<SandboxFolder>C:\\Job</SandboxFolder>
<ReadOnly>false</ReadOnly>
</MappedFolder>
</MappedFolders>
<VGpu>Enable</VGpu>
<Networking>Enable</Networking>
<MemoryInMB>{memory_in_mb or 8192}</MemoryInMB>
<LogonCommand>
<Command>C:\\Assets\\Run-NakedTest.cmd</Command>
</LogonCommand>
</Configuration>"""

            tmp_wsb = Path(tempfile.gettempdir()) / f"{jid}.wsb"
            tmp_wsb.write_text(wsb_xml, encoding="utf-8")

            import os

            wsb_exe = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "WindowsSandbox.exe"
            if wsb_exe.exists():
                subprocess.Popen([str(wsb_exe), str(tmp_wsb)])
            else:
                subprocess.Popen(["cmd.exe", "/c", "start", "", str(tmp_wsb)])

            return {
                "success": True,
                "action": "win_sandbox_naked_test",
                "job_id": jid,
                "repo": repo_url,
                "branch": branch,
                "run_dir": str(job_dir),
                "message": f"Launched automated naked install test for {repo_url} in Windows Sandbox.",
            }

        if action == "win_sandbox_naked_test_status":
            if not job_id:
                return {"success": False, "error": "job_id is required for win_sandbox_naked_test_status"}
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            runs_root = repo_root.parent / "_sandbox_runs"
            job_dir = runs_root / job_id
            if not job_dir.is_dir():
                return {"success": False, "error": f"Unknown job: {job_id}"}
            result_path = job_dir / "RESULT.json"
            if not result_path.is_file():
                return {
                    "success": True,
                    "action": "win_sandbox_naked_test_status",
                    "job_id": job_id,
                    "status": "running",
                    "message": "Test is still running in Windows Sandbox...",
                }
            import json

            try:
                result_data = json.loads(result_path.read_text(encoding="utf-8-sig"))
                result_data.setdefault("status", "finished")
                result_data["success"] = True
                result_data["action"] = "win_sandbox_naked_test_status"
                result_data["job_id"] = job_id
                return result_data
            except Exception as e:
                return {"success": False, "job_id": job_id, "status": "error", "error": f"RESULT.json unreadable: {e}"}

        if action == "win_sandbox_naked_test_list":
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            runs_root = repo_root.parent / "_sandbox_runs"
            if not runs_root.is_dir():
                return {"success": True, "action": "win_sandbox_naked_test_list", "jobs": []}
            import json

            jobs = []
            for d in sorted(runs_root.iterdir(), reverse=True):
                if d.is_dir() and d.name.startswith("naked-"):
                    spec_file = d / "spec.json"
                    spec = {}
                    if spec_file.is_file():
                        try:
                            spec = json.loads(spec_file.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                    result_file = d / "RESULT.json"
                    result = None
                    status = "running"
                    if result_file.is_file():
                        try:
                            result = json.loads(result_file.read_text(encoding="utf-8-sig"))
                            status = "finished"
                        except Exception:
                            status = "error"
                    jobs.append(
                        {
                            "job_id": d.name,
                            "status": status,
                            "repo": spec.get("repo_url", ""),
                            "branch": spec.get("branch", "main"),
                            "pass": result.get("pass") if result else None,
                            "failed_step": result.get("failed_step", "") if result else "",
                            "note": result.get("note", "") if result else "",
                            "finished_utc": result.get("finished_utc") if result else None,
                        }
                    )
                    if len(jobs) >= 20:
                        break
            return {"success": True, "action": "win_sandbox_naked_test_list", "jobs": jobs}

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
