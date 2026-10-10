"""Windows Sandbox helper utilities for virtualization-mcp."""

import asyncio
import logging
import platform
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, ClassVar

import psutil

logger = logging.getLogger(__name__)

# Detached one-shot runs (wait=False). Kept to avoid GC of asyncio Tasks.
_SANDBOX_ONE_SHOT_TASKS: set[asyncio.Task[dict[str, Any]]] = set()


class WindowsSandboxError(Exception):
    """Base exception for Windows Sandbox operations."""

    pass


class WindowsSandboxHelper:
    """Helper class for Windows Sandbox operations."""

    # Windows Sandbox executable
    WSX_EXECUTABLE = r"C:\Windows\System32\WindowsSandbox.exe"

    # Default sandbox configuration
    DEFAULT_CONFIG: ClassVar[dict[str, Any]] = {
        "memory_in_mb": 4096,
        "vcpu_count": 2,
        "networking": True,
        "protected_client": True,
        "printer_redirection": False,
        "video_input_redirection": False,
        "gpu_redirection": False,
        "clipboard_redirection": True,
        "memory_redirection": False,
        "vsmb_share": True,
        "vsmb_share_path": "C:\\Users\\WDAGUtilityAccount\\Desktop",
    }

    def check_prerequisites(self) -> dict:
        """Check if Windows Sandbox prerequisites are met."""
        return {
            "os_ok": platform.system() == "Windows",
            "executable_exists": Path(self.WSX_EXECUTABLE).exists(),
            "ready": platform.system() == "Windows" and Path(self.WSX_EXECUTABLE).exists(),
        }

    def __init__(self, sandbox_dir: str | Path | None = None):
        """Initialize the Windows Sandbox helper.

        Args:
            sandbox_dir: Directory to store sandbox configuration files
        """
        if platform.system() != "Windows":
            raise WindowsSandboxError("Windows Sandbox is only available on Windows 10/11")

        if not Path(self.WSX_EXECUTABLE).exists():
            raise WindowsSandboxError("Windows Sandbox is not installed or not available on this system")

        self.sandbox_dir = Path(sandbox_dir or tempfile.gettempdir()) / "virtualization-mcp_sandboxes"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        # Track running sandboxes
        self._sandbox_processes: dict[str, dict] = {}

    @staticmethod
    def is_sandbox_running() -> bool:
        """Check if Windows Sandbox OS process is currently running."""
        sandbox_procs = {
            "windowssandbox.exe",
            "windowssandboxclient.exe",
            "windowssandboxserver.exe",
            "windowssandboxremotesession.exe",
            # Hyper-V worker backing the sandbox VM. It outlives the
            # user-mode processes after a kill; relaunching while it
            # still holds the partition wedges with zero LogonCommand
            # output (fleet 2026-09-20).
            "vmmemwindowssandbox.exe",
        }
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in sandbox_procs:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    @staticmethod
    def terminate_active_sandbox() -> bool:
        """Terminate any existing Windows Sandbox OS instances to allow fresh sandbox launch.

        Returns:
            True if an active instance was terminated.
        """
        sandbox_procs = {
            "windowssandbox.exe",
            "windowssandboxclient.exe",
            "windowssandboxserver.exe",
            "windowssandboxremotesession.exe",
            "vmmemwindowssandbox.exe",
        }
        terminated = False
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in sandbox_procs:
                    proc.terminate()
                    terminated = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if terminated:
            time.sleep(1.5)
        return terminated

    def _launch_wsb(self, wsb_path: Path) -> None:
        """Launch a .wsb file in Windows Sandbox (returns immediately)."""
        wsb_exe = Path(self.WSX_EXECUTABLE)
        if wsb_exe.exists():
            subprocess.Popen([str(wsb_exe), str(wsb_path)])
        else:
            subprocess.Popen(["cmd.exe", "/c", "start", "", str(wsb_path)])

    async def _run_oneshot(
        self,
        command: str,
        files: dict[str, bytes] | None = None,
        memory_mb: int = 2048,
        timeout: int = 120,
        collect: str | None = None,
    ) -> dict[str, Any]:
        """Run a command in a fresh ephemeral sandbox and return real output.

        Windows Sandbox exposes no guest-control channel: the only automation
        vector is MappedFolders + LogonCommand at boot (same pattern the
        naked-test pipeline uses). So this boots a throwaway instance whose
        LogonCommand runs the command, polls the mapped job folder for the
        result, then terminates the instance. Nothing is faked: stdout,
        stderr and the exit code come from the guest.

        Args:
            command: Command line executed in the guest via cmd.exe.
            files: Extra files staged into the job folder (guest: C:\\Job).
            memory_mb: RAM for the throwaway instance.
            timeout: Seconds to wait for boot + command completion.
            collect: Optional job-folder file whose bytes are returned in
                result["collected"] before cleanup (for download flows).

        Returns:
            Dict with status (completed|timeout), exit_code, stdout, stderr
            and job_dir (kept on failure for debugging).
        """
        from datetime import datetime

        if self.is_sandbox_running():
            raise WindowsSandboxError(
                "Windows Sandbox is already running (singleton). Terminate it first - a second instance cannot boot."
            )

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_dir = self.sandbox_dir / f"oneshot-{stamp}"
        job_dir.mkdir(parents=True, exist_ok=True)
        for rel, data in (files or {}).items():
            target = job_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

        run_cmd = (
            "@echo off\r\n"
            "cd /d C:\\Job\r\n"
            f"{command} > stdout.log 2> stderr.log\r\n"
            "echo %ERRORLEVEL% > exitcode.txt\r\n"
        )
        (job_dir / "run.cmd").write_text(run_cmd, encoding="utf-8")

        config = ET.Element("Configuration")
        vgpu = ET.SubElement(config, "VGpu")
        vgpu.text = "Disable"
        networking = ET.SubElement(config, "Networking")
        networking.text = "Default"
        mem = ET.SubElement(config, "MemoryInMB")
        mem.text = str(memory_mb)
        mapped = ET.SubElement(config, "MappedFolders")
        mf = ET.SubElement(mapped, "MappedFolder")
        host = ET.SubElement(mf, "HostFolder")
        host.text = str(job_dir.resolve())
        guest = ET.SubElement(mf, "SandboxFolder")
        guest.text = "C:\\Job"
        ro = ET.SubElement(mf, "ReadOnly")
        ro.text = "false"
        logon = ET.SubElement(config, "LogonCommand")
        cmd_el = ET.SubElement(logon, "Command")
        cmd_el.text = "cmd.exe /c C:\\Job\\run.cmd"
        wsb_path = job_dir / "oneshot.wsb"
        ET.ElementTree(config).write(wsb_path, encoding="utf-8", xml_declaration=True)

        self._launch_wsb(wsb_path)

        exit_file = job_dir / "exitcode.txt"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if exit_file.is_file():
                break
            await asyncio.sleep(2)

        def _read(name: str) -> str:
            try:
                return (job_dir / name).read_text(encoding="utf-8", errors="replace")
            except OSError:
                return ""

        if not exit_file.is_file():
            try:
                self.terminate_active_sandbox()
            except Exception as e:
                logger.debug(f"one-shot teardown best-effort failed: {e}")
            return {
                "status": "timeout",
                "exit_code": None,
                "stdout": _read("stdout.log"),
                "stderr": _read("stderr.log"),
                "job_dir": str(job_dir),
                "message": f"No result after {timeout}s (kept {job_dir}).",
            }

        await asyncio.sleep(1)  # let the log flush land
        try:
            exit_code = int(_read("exitcode.txt").strip())
        except ValueError:
            exit_code = 1
        result = {
            "status": "completed",
            "exit_code": exit_code,
            "stdout": _read("stdout.log").strip(),
            "stderr": _read("stderr.log").strip(),
            "job_dir": str(job_dir),
        }
        if collect:
            try:
                result["collected"] = (job_dir / collect).read_bytes()
            except OSError as e:
                logger.warning(f"one-shot collect {collect} failed: {e}")
                result["collected"] = None
        try:
            self.terminate_active_sandbox()
        except Exception as e:
            logger.debug(f"one-shot teardown best-effort failed: {e}")
        if result.get("collected") is None and collect:
            pass  # keep job_dir for debugging when collection failed
        else:
            shutil.rmtree(job_dir, ignore_errors=True)
            result.pop("job_dir", None)
        return result

    async def create_sandbox(
        self,
        name: str,
        memory_mb: int | None = None,
        vcpu_count: int | None = None,
        shared_folders: list[dict[str, str]] | None = None,
        template: str = "default",
        force_clean: bool = True,
    ) -> dict[str, Any]:
        """Create and start a new Windows Sandbox instance.

        Args:
            name: Name of the sandbox
            memory_mb: Memory in MB to allocate to the sandbox
            vcpu_count: Number of virtual CPUs to allocate
            shared_folders: List of folders to share with the sandbox
            template: Template name for sandbox configuration
            force_clean: If True, automatically terminate existing singleton Windows Sandbox sessions.

        Returns:
            Dictionary with sandbox information
        """
        if force_clean:
            self.terminate_active_sandbox()
        elif self.is_sandbox_running():
            raise WindowsSandboxError(
                "Windows Sandbox is already running (singleton constraint). Use force_clean=True to replace."
            )

        # Create sandbox directory
        sandbox_dir = self.sandbox_dir / name
        sandbox_dir.mkdir(exist_ok=True)

        # Create WSB configuration
        wsb_path = sandbox_dir / f"{name}.wsb"
        self._create_wsb_config(
            wsb_path=wsb_path,
            memory_mb=memory_mb or self.DEFAULT_CONFIG["memory_in_mb"],
            vcpu_count=vcpu_count or self.DEFAULT_CONFIG["vcpu_count"],
            shared_folders=shared_folders or [],
        )

        # Start the sandbox
        process = await asyncio.create_subprocess_exec(
            self.WSX_EXECUTABLE,
            str(wsb_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # Store process information
        self._sandbox_processes[name] = {
            "process": process,
            "wsb_path": wsb_path,
            "sandbox_dir": sandbox_dir,
            "start_time": time.time(),
            "status": "running",
        }

        return {
            "name": name,
            "status": "running",
            "pid": process.pid,
            "wsb_path": str(wsb_path),
            "sandbox_dir": str(sandbox_dir),
        }

    async def execute_command(
        self,
        sandbox_name: str,
        command: str,
        working_dir: str | None = None,
        wait: bool = True,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Execute a command in a fresh ephemeral Windows Sandbox.

        Windows Sandbox is a singleton with no guest-control channel, so a
        command cannot be injected into an already-running instance. This
        boots a throwaway instance whose LogonCommand runs the command and
        returns the real stdout/stderr/exit code. If a sandbox is already
        running, an explicit busy error is returned instead of fake output.

        Args:
            sandbox_name: Label for the run (ephemeral, not a live handle).
            command: Command to execute in the guest.
            working_dir: Guest working directory (prefixes the command).
            wait: Wait for completion. False returns immediately and runs
                detached (output is lost - prefer wait=True).
            timeout: Seconds to wait for boot + completion.

        Returns:
            Dictionary with real command execution results.
        """
        full_command = f'cd /d "{working_dir}" && {command}' if working_dir else command
        if not wait:
            task = asyncio.create_task(self._run_oneshot(full_command, timeout=timeout))
            _SANDBOX_ONE_SHOT_TASKS.add(task)
            task.add_done_callback(_SANDBOX_ONE_SHOT_TASKS.discard)
            return {"status": "started", "sandbox": sandbox_name, "command": command}
        result = await self._run_oneshot(full_command, timeout=timeout)
        result["sandbox"] = sandbox_name
        result["command"] = command
        return result

    async def upload_file(
        self,
        sandbox_name: str,
        source_path: str | Path,
        destination_path: str | Path | None = None,
        timeout: int = 180,
    ) -> dict[str, Any]:
        """Upload a host file into a fresh ephemeral Windows Sandbox.

        The payload is staged into the mapped job folder and copied to its
        guest destination by the LogonCommand. The copy really happens -
        a non-zero guest exit code raises instead of reporting success.

        Args:
            sandbox_name: Label for the run.
            source_path: Host file to upload.
            destination_path: Guest destination (default: sandbox Desktop).
            timeout: Seconds to wait for boot + copy.

        Returns:
            Dictionary with upload results.
        """
        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        dest = str(destination_path) if destination_path else f"C:\\Users\\WDAGUtilityAccount\\Desktop\\{source.name}"
        staged = f"payload_{source.name}"
        result = await self._run_oneshot(
            f'copy /Y "C:\\Job\\{staged}" "{dest}"',
            files={staged: source.read_bytes()},
            timeout=timeout,
        )
        if result.get("status") != "completed" or result.get("exit_code", 1) != 0:
            raise WindowsSandboxError(
                f"Failed to copy file in sandbox: {result.get('stderr', result.get('message', 'Unknown error'))}"
            )

        return {
            "status": "success",
            "source_path": str(source),
            "destination_path": dest,
            "size": source.stat().st_size,
        }

    async def download_file(
        self,
        sandbox_name: str,
        source_path: str | Path,
        destination_path: str | Path | None = None,
        timeout: int = 180,
    ) -> dict[str, Any]:
        """Download a file out of a fresh ephemeral Windows Sandbox.

        The guest copies the source into the mapped job folder and the host
        reads it back - the bytes really cross the boundary. A missing guest
        file raises instead of reporting success.

        Args:
            sandbox_name: Label for the run.
            source_path: Guest path of the file to download.
            destination_path: Host destination (default: cwd + file name).
            timeout: Seconds to wait for boot + copy.

        Returns:
            Dictionary with download results.
        """
        guest_src = str(source_path)
        guest_name = guest_src.replace("/", "\\").split("\\")[-1] or "payload.bin"
        dest = Path(destination_path) if destination_path else Path.cwd() / guest_name

        result = await self._run_oneshot(
            f'copy /Y "{guest_src}" "C:\\Job\\payload.bin"',
            timeout=timeout,
            collect="payload.bin",
        )
        payload = result.get("collected")
        if result.get("status") != "completed" or payload is None:
            raise WindowsSandboxError(
                f"Failed to download {guest_src} from sandbox: "
                f"{result.get('stderr', result.get('message', 'Unknown error'))}"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)

        return {
            "status": "success",
            "source_path": guest_src,
            "destination_path": str(dest),
            "size": dest.stat().st_size,
        }

    async def terminate_sandbox(self, sandbox_name: str, force: bool = False) -> dict[str, Any]:
        """Terminate a running sandbox.

        Args:
            sandbox_name: Name of the sandbox to terminate
            force: Whether to force termination

        Returns:
            Dictionary with termination status
        """
        if sandbox_name not in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox '{sandbox_name}' not found")

        process_info = self._sandbox_processes[sandbox_name]
        process = process_info["process"]

        try:
            if force:
                # Forcefully terminate the process tree
                self._kill_process_tree(process.pid)
            else:
                # Try graceful termination first
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except TimeoutError:
                    # Force terminate if it doesn't exit gracefully
                    self._kill_process_tree(process.pid)

            # Clean up
            await self._cleanup_sandbox(sandbox_name)

            # The registry only tracks the launcher stub (long exited). The
            # real VM is the OS singleton - terminate it as well.
            singleton = self.terminate_active_sandbox()

            return {"status": "terminated", "sandbox": sandbox_name, "force": force, "singleton_terminated": singleton}

        except Exception as e:
            raise WindowsSandboxError(f"Failed to terminate sandbox: {e!s}") from e

    async def list_sandboxes(self) -> list[dict[str, Any]]:
        """List tracked sandboxes plus the live OS singleton state.

        The registry only holds sandboxes this process launched; the
        singleton_running flag reports the actual Windows Sandbox VM
        regardless of who started it.

        Returns:
            List of dictionaries with sandbox information
        """
        singleton_running = self.is_sandbox_running()
        result = []
        for name, info in self._sandbox_processes.items():
            process = info["process"]
            alive = process.returncode is None
            result.append(
                {
                    "name": name,
                    "pid": process.pid,
                    "status": "running" if alive and singleton_running else "exited",
                    "exit_code": process.returncode,
                    "wsb_path": str(info["wsb_path"]),
                    "start_time": info["start_time"],
                    "singleton_running": singleton_running,
                }
            )
        if singleton_running and not result:
            result.append(
                {
                    "name": "<unmanaged-singleton>",
                    "pid": None,
                    "status": "running",
                    "exit_code": None,
                    "wsb_path": "",
                    "start_time": 0.0,
                    "singleton_running": True,
                }
            )
        return result

    async def _cleanup_sandbox(self, sandbox_name: str) -> None:
        """Clean up resources for a sandbox.

        Args:
            sandbox_name: Name of the sandbox to clean up
        """
        if sandbox_name in self._sandbox_processes:
            # Clean up process
            process_info = self._sandbox_processes.pop(sandbox_name)
            process = process_info["process"]

            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except (TimeoutError, ProcessLookupError):
                    pass

            # Clean up temporary files
            sandbox_dir = process_info.get("sandbox_dir")
            if sandbox_dir and sandbox_dir.exists():
                try:
                    await asyncio.to_thread(shutil.rmtree, sandbox_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up sandbox directory {sandbox_dir}: {e}")

    def _create_wsb_config(
        self,
        wsb_path: str | Path,
        memory_mb: int,
        vcpu_count: int,
        shared_folders: list[dict[str, str]],
        logon_command: str | None = None,
    ) -> None:
        """Create a Windows Sandbox configuration file.

        Args:
            wsb_path: Path to save the WSB file
            memory_mb: Memory in MB to allocate to the sandbox
            vcpu_count: Number of virtual CPUs to allocate
            shared_folders: List of folders to share with the sandbox
            logon_command: Guest-side command run at logon (must reference
                a guest path such as C:\\Job\\run.cmd - host paths do not
                exist in the guest). Omitted when None.
        """
        # Create XML configuration
        config = ET.Element("Configuration")

        # Add memory settings
        vgpu = ET.SubElement(config, "VGpu")
        vgpu.text = "Enable"

        networking = ET.SubElement(config, "Networking")
        networking.text = "Default"

        mapped_folders = ET.SubElement(config, "MappedFolders")

        # Add shared folders
        for i, folder in enumerate(shared_folders):
            host_path = folder.get("host_path")
            sandbox_path = folder.get("sandbox_path", f"C:\\shared\\{i}")
            read_only = folder.get("read_only", "true").lower() == "true"

            if not host_path or not Path(host_path).exists():
                continue

            mf = ET.SubElement(mapped_folders, "MappedFolder")

            host = ET.SubElement(mf, "HostFolder")
            host.text = str(Path(host_path).resolve())

            sandbox = ET.SubElement(mf, "SandboxFolder")
            sandbox.text = sandbox_path

            ro = ET.SubElement(mf, "ReadOnly")
            ro.text = "true" if read_only else "false"

        # Optional guest-side logon command (guest paths only).
        if logon_command:
            logon_el = ET.SubElement(config, "LogonCommand")
            command = ET.SubElement(logon_el, "Command")
            command.text = logon_command

        # Save the WSB file
        tree = ET.ElementTree(config)
        tree.write(wsb_path, encoding="utf-8", xml_declaration=True)

    def _kill_process_tree(self, pid: int) -> None:
        """Kill a process and all its children.

        Args:
            pid: Process ID to kill
        """
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Kill children first
            for child in children:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Kill parent
            try:
                parent.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            # Wait for processes to terminate
            _gone, still_alive = psutil.wait_procs([*children, parent], timeout=5)

            # Force kill any remaining processes
            for p in still_alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except psutil.NoSuchProcess:
            pass

    async def execute_in_sandbox(
        self,
        name: str,
        command: str,
        timeout_seconds: int = 120,
    ) -> dict[str, Any]:
        """Execute a shell command in a fresh ephemeral Windows Sandbox.

        Boots a throwaway instance whose LogonCommand runs the command and
        returns the real stdout/stderr/exit code (same primitive the
        naked-test pipeline uses). There is no shared-folder watcher -
        the previous "scheduled_in_shared_folder" success never executed
        anything. A busy singleton raises WindowsSandboxError.

        Args:
            name: Label for the run.
            command: Shell command or script snippet to execute.
            timeout_seconds: Maximum time to wait for boot + execution.

        Returns:
            Dict with success, exit_code, stdout, stderr.
        """
        result = await self._run_oneshot(command, timeout=timeout_seconds)
        return {
            "success": result.get("status") == "completed" and result.get("exit_code", 1) == 0,
            "sandbox_name": name,
            "command": command,
            "status": result.get("status"),
            "exit_code": result.get("exit_code"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "job_dir": result.get("job_dir", ""),
        }

    def __del__(self):
        """Clean up resources on object destruction."""
        for name in list(self._sandbox_processes.keys()):
            try:
                _cleanup_task = asyncio.create_task(self._cleanup_sandbox(name))  # noqa: RUF006
            except Exception as e:
                logger.error(f"Error cleaning up sandbox {name}: {e}")
