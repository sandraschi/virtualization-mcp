"""Windows Sandbox helper utilities for virtualization-mcp."""

import asyncio
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class WindowsSandboxError(Exception):
    """Base exception for Windows Sandbox operations."""

    pass


class WindowsSandboxHelper:
    """Helper class for Windows Sandbox operations."""

    # Windows Sandbox executable
    WSX_EXECUTABLE = r"C:\Windows\System32\WindowsSandbox.exe"

    # Default sandbox configuration
    DEFAULT_CONFIG = {
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

    def __init__(self, sandbox_dir: str | Path | None = None):
        """Initialize the Windows Sandbox helper.

        Args:
            sandbox_dir: Directory to store sandbox configuration files
        """
        if platform.system() != "Windows":
            raise WindowsSandboxError("Windows Sandbox is only available on Windows 10/11")

        if not os.path.exists(self.WSX_EXECUTABLE):
            raise WindowsSandboxError(
                "Windows Sandbox is not installed or not available on this system"
            )

        self.sandbox_dir = (
            Path(sandbox_dir or tempfile.gettempdir()) / "virtualization-mcp_sandboxes"
        )
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        # Track running sandboxes
        self._sandbox_processes: dict[str, dict] = {}

    async def create_sandbox(
        self,
        name: str,
        memory_mb: int | None = None,
        vcpu_count: int | None = None,
        shared_folders: list[dict[str, str]] | None = None,
        template: str = "default",
    ) -> dict[str, Any]:
        """Create and start a new Windows Sandbox instance.

        Args:
            name: Name of the sandbox
            memory_mb: Memory in MB to allocate to the sandbox
            vcpu_count: Number of virtual CPUs to allocate
            shared_folders: List of folders to share with the sandbox
            template: Template name for sandbox configuration

        Returns:
            Dictionary with sandbox information
        """
        if name in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox with name '{name}' already exists")

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
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Execute a command in the sandbox.

        Args:
            sandbox_name: Name of the sandbox
            command: Command to execute
            working_dir: Working directory for the command
            wait: Whether to wait for command completion
            timeout: Timeout in seconds

        Returns:
            Dictionary with command execution results
        """
        if sandbox_name not in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox '{sandbox_name}' not found")

        # Create a temporary batch file in the sandbox
        temp_bat = self._create_temp_file_in_sandbox(
            sandbox_name,
            f"@echo off\r\n{command}\r\necho %ERRORLEVEL% > %TEMP%\\cmd_exit_code.txt\r\n",
            "cmd.bat",
        )

        # Create a command to run the batch file and capture output
        cmd = f'cmd.exe /c "{temp_bat} > %TEMP%\\cmd_output.txt 2>&1 & type %TEMP%\\cmd_output.txt & type %TEMP%\\cmd_exit_code.txt"'

        # Execute the command
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f'Start-Process -FilePath "{self.WSX_EXECUTABLE}" -ArgumentList "{self._sandbox_processes[sandbox_name]["wsb_path"]}" -Wait -NoNewWindow -PassThru | Wait-Process',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if wait:
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                exit_code = process.returncode

                # Get command output and exit code
                output = stdout.decode("utf-8", errors="replace").strip()
                error = stderr.decode("utf-8", errors="replace").strip()

                # Clean up temporary files
                self._delete_temp_file_in_sandbox(sandbox_name, temp_bat)

                return {
                    "status": "completed",
                    "exit_code": exit_code,
                    "stdout": output,
                    "stderr": error,
                }
            except asyncio.TimeoutError:
                process.terminate()
                return {
                    "status": "timeout",
                    "message": f"Command timed out after {timeout} seconds",
                }
        else:
            return {"status": "started", "pid": process.pid}

    async def upload_file(
        self,
        sandbox_name: str,
        source_path: str | Path,
        destination_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Upload a file to the sandbox.

        Args:
            sandbox_name: Name of the sandbox
            source_path: Path to the source file
            destination_path: Destination path in the sandbox

        Returns:
            Dictionary with upload results
        """
        if sandbox_name not in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox '{sandbox_name}' not found")

        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Default destination is the sandbox's desktop
        if not destination_path:
            destination_path = Path("C:\\Users\\WDAGUtilityAccount\\Desktop") / source_path.name
        else:
            destination_path = Path(destination_path)

        # Create a temporary file in the sandbox's shared folder
        temp_dir = self.sandbox_dir / sandbox_name / "shared"
        temp_dir.mkdir(exist_ok=True, parents=True)

        temp_file = temp_dir / source_path.name
        shutil.copy2(source_path, temp_file)

        # Move the file to the destination using a command
        move_cmd = f'move /Y "C:\\shared\\{source_path.name}" "{destination_path}"'
        result = await self.execute_command(sandbox_name, move_cmd)

        if result.get("exit_code", 1) != 0:
            raise WindowsSandboxError(
                f"Failed to move file in sandbox: {result.get('stderr', 'Unknown error')}"
            )

        return {
            "status": "success",
            "source_path": str(source_path),
            "destination_path": str(destination_path),
            "size": source_path.stat().st_size,
        }

    async def download_file(
        self,
        sandbox_name: str,
        source_path: str | Path,
        destination_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Download a file from the sandbox.

        Args:
            sandbox_name: Name of the sandbox
            source_path: Path to the source file in the sandbox
            destination_path: Destination path on the host

        Returns:
            Dictionary with download results
        """
        if sandbox_name not in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox '{sandbox_name}' not found")

        source_path = Path(source_path)
        if not destination_path:
            destination_path = Path.cwd() / source_path.name
        else:
            destination_path = Path(destination_path)

        # Create a temporary directory in the sandbox's shared folder
        temp_dir = self.sandbox_dir / sandbox_name / "shared"
        temp_dir.mkdir(exist_ok=True, parents=True)

        # Copy the file to the shared folder
        copy_cmd = f'copy /Y "{source_path}" C:\\shared\\'
        result = await self.execute_command(sandbox_name, copy_cmd)

        if result.get("exit_code", 1) != 0:
            raise WindowsSandboxError(
                f"Failed to copy file to shared folder: {result.get('stderr', 'Unknown error')}"
            )

        # Copy from shared folder to destination
        temp_file = temp_dir / source_path.name
        if not temp_file.exists():
            raise FileNotFoundError(f"File not found in shared folder: {temp_file}")

        shutil.copy2(temp_file, destination_path)

        # Clean up
        temp_file.unlink(missing_ok=True)

        return {
            "status": "success",
            "source_path": str(source_path),
            "destination_path": str(destination_path),
            "size": destination_path.stat().st_size,
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
                except asyncio.TimeoutError:
                    # Force terminate if it doesn't exit gracefully
                    self._kill_process_tree(process.pid)

            # Clean up
            await self._cleanup_sandbox(sandbox_name)

            return {"status": "terminated", "sandbox": sandbox_name, "force": force}

        except Exception as e:
            raise WindowsSandboxError(f"Failed to terminate sandbox: {str(e)}")

    async def list_sandboxes(self) -> list[dict[str, Any]]:
        """List all active sandboxes.

        Returns:
            List of dictionaries with sandbox information
        """
        result = []
        for name, info in self._sandbox_processes.items():
            process = info["process"]
            result.append(
                {
                    "name": name,
                    "pid": process.pid,
                    "status": "running" if process.returncode is None else "exited",
                    "exit_code": process.returncode,
                    "wsb_path": str(info["wsb_path"]),
                    "start_time": info["start_time"],
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
                except (ProcessLookupError, asyncio.TimeoutError):
                    pass

            # Clean up temporary files
            sandbox_dir = process_info.get("sandbox_dir")
            if sandbox_dir and sandbox_dir.exists():
                try:
                    shutil.rmtree(sandbox_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up sandbox directory {sandbox_dir}: {e}")

    def _create_wsb_config(
        self,
        wsb_path: str | Path,
        memory_mb: int,
        vcpu_count: int,
        shared_folders: list[dict[str, str]],
    ) -> None:
        """Create a Windows Sandbox configuration file.

        Args:
            wsb_path: Path to save the WSB file
            memory_mb: Memory in MB to allocate to the sandbox
            vcpu_count: Number of virtual CPUs to allocate
            shared_folders: List of folders to share with the sandbox
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

            if not host_path or not os.path.exists(host_path):
                continue

            mf = ET.SubElement(mapped_folders, "MappedFolder")

            host = ET.SubElement(mf, "HostFolder")
            host.text = os.path.abspath(host_path)

            sandbox = ET.SubElement(mf, "SandboxFolder")
            sandbox.text = sandbox_path

            ro = ET.SubElement(mf, "ReadOnly")
            ro.text = "true" if read_only else "false"

        # Add logon command to map network drives
        logon_command = ET.SubElement(config, "LogonCommand")
        command = ET.SubElement(logon_command, "Command")

        # Create a batch file to map network drives
        batch_commands = ["@echo off"]
        for i, folder in enumerate(shared_folders):
            if not folder.get("host_path"):
                continue

            drive_letter = folder.get("drive_letter")
            if drive_letter and len(drive_letter) == 1 and drive_letter.isalpha():
                drive_letter = f"{drive_letter.upper()}:\\"
                sandbox_path = folder.get("sandbox_path", f"C:\\shared\\{i}")
                batch_commands.append(f"net use {drive_letter} {sandbox_path}")

        batch_commands.append("exit 0")
        batch_content = "\r\n".join(batch_commands)

        # Save batch file to a shared folder
        batch_path = self.sandbox_dir / "startup.bat"
        with open(batch_path, "w") as f:
            f.write(batch_content)

        command.text = f'C:\\Windows\\System32\\cmd.exe /c "{batch_path}"'

        # Save the WSB file
        tree = ET.ElementTree(config)
        tree.write(wsb_path, encoding="utf-8", xml_declaration=True)

    def _create_temp_file_in_sandbox(self, sandbox_name: str, content: str, filename: str) -> str:
        """Create a temporary file in the sandbox's shared folder.

        Args:
            sandbox_name: Name of the sandbox
            content: File content
            filename: Name of the file

        Returns:
            Path to the created file in the sandbox
        """
        if sandbox_name not in self._sandbox_processes:
            raise WindowsSandboxError(f"Sandbox '{sandbox_name}' not found")

        sandbox_dir = self.sandbox_dir / sandbox_name
        shared_dir = sandbox_dir / "shared"
        shared_dir.mkdir(exist_ok=True, parents=True)

        temp_file = shared_dir / filename
        with open(temp_file, "w") as f:
            f.write(content)

        return f"C:\\shared\\{filename}"

    def _delete_temp_file_in_sandbox(self, sandbox_name: str, filename: str) -> None:
        """Delete a temporary file from the sandbox's shared folder.

        Args:
            sandbox_name: Name of the sandbox
            filename: Name of the file to delete
        """
        if sandbox_name not in self._sandbox_processes:
            return

        sandbox_dir = self.sandbox_dir / sandbox_name
        shared_dir = sandbox_dir / "shared"

        if not shared_dir.exists():
            return

        temp_file = shared_dir / Path(filename).name
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file}: {e}")

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
            gone, still_alive = psutil.wait_procs(children + [parent], timeout=5)

            # Force kill any remaining processes
            for p in still_alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except psutil.NoSuchProcess:
            pass

    def __del__(self):
        """Clean up resources on object destruction."""
        for name in list(self._sandbox_processes.keys()):
            try:
                asyncio.create_task(self._cleanup_sandbox(name))
            except Exception as e:
                logger.error(f"Error cleaning up sandbox {name}: {e}")
