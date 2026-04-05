"""
Docker Sandbox Backend

Low-level Docker operations for ephemeral and stateful code execution.
No FastMCP dependencies — pure Docker SDK logic.
"""

import logging
import os
import tempfile
import uuid
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Supported languages and their Docker images + run commands
LANGUAGE_CONFIG: dict[str, dict[str, Any]] = {
    "python": {
        "image": "python:3.13-slim",
        "command": lambda code: ["python", "-c", code],
        "file_ext": ".py",
        "file_command": lambda path: ["python", path],
    },
    "javascript": {
        "image": "node:22-slim",
        "command": lambda code: ["node", "-e", code],
        "file_ext": ".js",
        "file_command": lambda path: ["node", path],
    },
    "bash": {
        "image": "ubuntu:24.04",
        "command": lambda code: ["bash", "-c", code],
        "file_ext": ".sh",
        "file_command": lambda path: ["bash", path],
    },
}

# Default resource limits — tunable via env vars
DEFAULT_MEM_LIMIT = os.environ.get("SANDBOX_MEM_LIMIT", "256m")
DEFAULT_CPU_QUOTA = int(os.environ.get("SANDBOX_CPU_QUOTA", "50000"))  # 50% of 1 core
DEFAULT_CPU_PERIOD = int(os.environ.get("SANDBOX_CPU_PERIOD", "100000"))
DEFAULT_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "30"))

# In-memory session registry: sandbox_id -> container object
_sessions: dict[str, Any] = {}


def _get_client():
    """Get Docker client. Raises RuntimeError if Docker not available."""
    try:
        import docker
        return docker.from_env()
    except ImportError:
        raise RuntimeError("docker package not installed. Run: uv add docker")
    except Exception as e:
        raise RuntimeError(f"Docker not available: {e}. Is Docker Desktop running?")


def _decode(raw: bytes | None) -> str:
    if not raw:
        return ""
    return raw.decode("utf-8", errors="replace").strip()


# ---------------------------------------------------------------------------
# Ephemeral execution
# ---------------------------------------------------------------------------

def execute_code(
    code: str,
    language: Literal["python", "javascript", "bash"] = "python",
    timeout: int = DEFAULT_TIMEOUT,
    network_enabled: bool = False,
) -> dict[str, Any]:
    """Run a code snippet in a throwaway container. Container is removed after execution."""
    if language not in LANGUAGE_CONFIG:
        return {
            "success": False,
            "error": f"Unsupported language '{language}'. Supported: {list(LANGUAGE_CONFIG)}",
        }

    cfg = LANGUAGE_CONFIG[language]
    client = _get_client()

    try:
        result = client.containers.run(
            image=cfg["image"],
            command=cfg["command"](code),
            mem_limit=DEFAULT_MEM_LIMIT,
            cpu_period=DEFAULT_CPU_PERIOD,
            cpu_quota=DEFAULT_CPU_QUOTA,
            network_disabled=not network_enabled,
            remove=True,
            stdout=True,
            stderr=True,
            timeout=timeout,
        )
        return {
            "success": True,
            "output": _decode(result),
            "stderr": "",
            "exit_code": 0,
            "language": language,
        }
    except Exception as e:
        try:
            import docker.errors
            if isinstance(e, docker.errors.ContainerError):
                return {
                    "success": False,
                    "output": "",
                    "stderr": _decode(e.stderr),
                    "exit_code": e.exit_status,
                    "language": language,
                    "error": f"Container exited with code {e.exit_status}",
                }
        except ImportError:
            pass
        return {
            "success": False,
            "output": "",
            "stderr": "",
            "exit_code": -1,
            "language": language,
            "error": str(e),
        }


def execute_file(
    host_path: str,
    language: Literal["python", "javascript", "bash"] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    network_enabled: bool = False,
) -> dict[str, Any]:
    """Run a host file in a throwaway container. Language auto-detected from extension."""
    if not os.path.isfile(host_path):
        return {"success": False, "error": f"File not found: {host_path}"}

    if language is None:
        ext = os.path.splitext(host_path)[1].lower()
        ext_map = {".py": "python", ".js": "javascript", ".sh": "bash"}
        language = ext_map.get(ext)
        if language is None:
            return {
                "success": False,
                "error": f"Cannot detect language from extension '{ext}'. Specify language explicitly.",
            }

    if language not in LANGUAGE_CONFIG:
        return {"success": False, "error": f"Unsupported language '{language}'"}

    cfg = LANGUAGE_CONFIG[language]
    client = _get_client()
    container_path = f"/sandbox/code{cfg['file_ext']}"

    try:
        import io, tarfile
        container = client.containers.create(
            image=cfg["image"],
            command=cfg["file_command"](container_path),
            mem_limit=DEFAULT_MEM_LIMIT,
            cpu_period=DEFAULT_CPU_PERIOD,
            cpu_quota=DEFAULT_CPU_QUOTA,
            network_disabled=not network_enabled,
        )
        try:
            with open(host_path, "rb") as f:
                file_data = f.read()
            tar_buf = io.BytesIO()
            with tarfile.open(fileobj=tar_buf, mode="w") as tar:
                info = tarfile.TarInfo(name=f"code{cfg['file_ext']}")
                info.size = len(file_data)
                tar.addfile(info, io.BytesIO(file_data))
            tar_buf.seek(0)
            container.put_archive("/sandbox/", tar_buf)
            container.start()
            exit_code = container.wait(timeout=timeout)["StatusCode"]
            stdout = _decode(container.logs(stdout=True, stderr=False))
            stderr = _decode(container.logs(stdout=False, stderr=True))
            return {
                "success": exit_code == 0,
                "output": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "language": language,
                "host_path": host_path,
            }
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass
    except Exception as e:
        return {"success": False, "error": str(e), "host_path": host_path}


# ---------------------------------------------------------------------------
# Stateful sessions
# ---------------------------------------------------------------------------

def session_create(
    image: str = "python:3.13-slim",
    name: str | None = None,
) -> dict[str, Any]:
    """Create a persistent container session. Returns sandbox_id."""
    client = _get_client()
    sandbox_id = str(uuid.uuid4())[:8]
    container_name = name or f"sandbox-{sandbox_id}"

    try:
        container = client.containers.run(
            image=image,
            name=container_name,
            command=["sleep", "3600"],
            mem_limit=DEFAULT_MEM_LIMIT,
            cpu_period=DEFAULT_CPU_PERIOD,
            cpu_quota=DEFAULT_CPU_QUOTA,
            network_disabled=True,
            detach=True,
            remove=False,
        )
        _sessions[sandbox_id] = container
        return {
            "success": True,
            "sandbox_id": sandbox_id,
            "container_name": container_name,
            "image": image,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def session_run(sandbox_id: str, command: str) -> dict[str, Any]:
    """Run a shell command in an existing session. State persists between calls."""
    container = _sessions.get(sandbox_id)
    if container is None:
        return {"success": False, "error": f"Sandbox '{sandbox_id}' not found. Use session_create first."}

    try:
        exit_code, output = container.exec_run(
            cmd=["bash", "-c", command],
            stdout=True,
            stderr=True,
            demux=False,
        )
        return {
            "success": exit_code == 0,
            "output": _decode(output),
            "exit_code": exit_code,
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "sandbox_id": sandbox_id}


def session_write_file(sandbox_id: str, container_path: str, content: str) -> dict[str, Any]:
    """Write a text file into a running sandbox session."""
    container = _sessions.get(sandbox_id)
    if container is None:
        return {"success": False, "error": f"Sandbox '{sandbox_id}' not found."}

    try:
        import io, tarfile
        data = content.encode("utf-8")
        filename = os.path.basename(container_path)
        dirpath = os.path.dirname(container_path) or "/"
        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w") as tar:
            info = tarfile.TarInfo(name=filename)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        tar_buf.seek(0)
        container.put_archive(dirpath, tar_buf)
        return {"success": True, "sandbox_id": sandbox_id, "path": container_path}
    except Exception as e:
        return {"success": False, "error": str(e), "sandbox_id": sandbox_id}


def session_read_file(sandbox_id: str, container_path: str) -> dict[str, Any]:
    """Read a text file from a running sandbox session."""
    container = _sessions.get(sandbox_id)
    if container is None:
        return {"success": False, "error": f"Sandbox '{sandbox_id}' not found."}

    try:
        import io, tarfile
        stream, _ = container.get_archive(container_path)
        tar_buf = io.BytesIO(b"".join(stream))
        with tarfile.open(fileobj=tar_buf) as tar:
            member = tar.getmembers()[0]
            content = tar.extractfile(member).read().decode("utf-8", errors="replace")
        return {"success": True, "sandbox_id": sandbox_id, "path": container_path, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e), "sandbox_id": sandbox_id}


def session_list() -> dict[str, Any]:
    """List all active sandbox sessions."""
    items = []
    dead = []
    for sid, container in _sessions.items():
        try:
            container.reload()
            items.append({
                "sandbox_id": sid,
                "container_name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
            })
        except Exception:
            dead.append(sid)
    for sid in dead:
        del _sessions[sid]
    return {"success": True, "sessions": items, "count": len(items)}


def session_destroy(sandbox_id: str) -> dict[str, Any]:
    """Stop and remove a sandbox session."""
    container = _sessions.pop(sandbox_id, None)
    if container is None:
        return {"success": False, "error": f"Sandbox '{sandbox_id}' not found."}
    try:
        container.remove(force=True)
        return {"success": True, "sandbox_id": sandbox_id, "message": "Sandbox destroyed"}
    except Exception as e:
        return {"success": False, "error": str(e), "sandbox_id": sandbox_id}
