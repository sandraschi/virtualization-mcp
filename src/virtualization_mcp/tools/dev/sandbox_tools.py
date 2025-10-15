"""
Sandbox Testing Tools for virtualization-mcp

Provides tools for quickly testing code in an isolated sandbox environment.
"""

import asyncio
import json
import logging
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SandboxType(str, Enum):
    """Types of sandbox environments."""

    WINDOWS_SANDBOX = "windows_sandbox"
    DOCKER = "docker"
    VENV = "venv"


class ResourceUsage(BaseModel):
    """Resource usage statistics for a sandbox."""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0


class SandboxState(str, Enum):
    """Possible states of a sandbox."""

    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


class NetworkConfig(BaseModel):
    """Network configuration for a sandbox."""

    enabled: bool = True
    allow_outbound: bool = True
    allow_inbound: bool = False
    hostname: str | None = None
    dns_servers: list[str] = ["8.8.8.8", "1.1.1.1"]
    ports: dict[int, int] = Field(
        default_factory=dict, description="Port mappings (host_port: container_port)"
    )


class ResourceLimits(BaseModel):
    """Resource limits for a sandbox."""

    cpu_count: int | None = None
    memory_mb: int | None = None
    disk_mb: int | None = None
    process_limit: int | None = None
    network_bandwidth_mbps: float | None = None

    @field_validator("memory_mb", "disk_mb")
    @classmethod
    def positive_number(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Must be a positive number")
        return v


class TestResult(BaseModel):
    """Result of a sandbox test."""

    success: bool
    output: str
    error: str | None = None
    execution_time: float  # in seconds
    sandbox_type: SandboxType
    files_generated: list[str] = Field(default_factory=list)
    resource_usage: ResourceUsage | None = None
    exit_code: int | None = None
    warnings: list[str] = Field(default_factory=list)


@dataclass
class SandboxInfo:
    """Information about a sandbox instance."""

    name: str
    sandbox_type: SandboxType
    directory: Path
    state: SandboxState = SandboxState.CREATING
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime | None = None
    process: asyncio.subprocess.Process | None = None
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network_config: NetworkConfig = field(default_factory=NetworkConfig)
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    persistent_storage: bool = False
    persistent_path: Path | None = None

    class Config:
        arbitrary_types_allowed = True


class SandboxTester:
    """Manages sandbox environments for testing code with advanced features."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the sandbox tester with advanced configuration.

        Args:
            base_dir: Base directory for sandbox files (default: system temp)
        """
        self.base_dir = Path(base_dir or tempfile.gettempdir()) / "virtualization-mcp_sandboxes"
        self.base_dir.mkdir(exist_ok=True, parents=True)

        # Track active sandboxes and their locks
        self._active_sandboxes: dict[str, SandboxInfo] = {}
        self._sandbox_locks: dict[str, asyncio.Lock] = {}

        # Platform-specific setup
        self.platform = platform.system().lower()
        self._resource_monitor_task: asyncio.Task | None = None
        self._monitoring = asyncio.Event()
        self._initialized = False

        logger.info(f"Initialized SandboxTester with base directory: {self.base_dir}")

    async def initialize(self):
        """Initialize the sandbox tester by starting required background tasks.

        This should be called when the asyncio event loop is running.
        """
        if not self._initialized:
            self._monitoring.set()
            self._resource_monitor_task = asyncio.create_task(self._start_resource_monitor())
            await self._load_existing_sandboxes()
            self._initialized = True
            logger.info("SandboxTester background tasks started")

    async def _start_resource_monitor(self):
        """Start monitoring resource usage for all sandboxes."""
        self._monitoring.set()
        while self._monitoring.is_set():
            await asyncio.sleep(5)  # Update every 5 seconds
            for sandbox in list(self._active_sandboxes.values()):
                if sandbox.process and sandbox.process.returncode is None:
                    try:
                        await self._update_resource_usage(sandbox)
                    except Exception as e:
                        logger.warning(f"Error updating resource usage for {sandbox.name}: {e}")

    async def _update_resource_usage(self, sandbox: SandboxInfo):
        """Update resource usage for a sandbox."""
        if not sandbox.process or not sandbox.process.pid:
            return

        try:
            process = psutil.Process(sandbox.process.pid)
            with process.oneshot():
                sandbox.resource_usage.cpu_percent = process.cpu_percent()
                sandbox.resource_usage.memory_mb = process.memory_info().rss / (1024 * 1024)

                # Get disk and network I/O if available
                try:
                    io_counters = process.io_counters()
                    sandbox.resource_usage.disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                    sandbox.resource_usage.disk_write_mb = io_counters.write_bytes / (1024 * 1024)
                except (psutil.AccessDenied, NotImplementedError):
                    pass

                # Update last used time
                sandbox.last_used = datetime.utcnow()
        except psutil.NoSuchProcess:
            sandbox.state = SandboxState.STOPPED

    async def _load_existing_sandboxes(self):
        """Load existing sandboxes from disk."""
        for entry in self.base_dir.iterdir():
            if entry.is_dir() and (entry / "sandbox.json").exists():
                try:
                    with open(entry / "sandbox.json") as f:
                        data = json.load(f)

                    sandbox = SandboxInfo(
                        name=data["name"],
                        sandbox_type=SandboxType(data["sandbox_type"]),
                        directory=entry,
                        state=SandboxState(data.get("state", "stopped")),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        last_used=datetime.fromisoformat(data["last_used"])
                        if data.get("last_used")
                        else None,
                        resource_limits=ResourceLimits(**data.get("resource_limits", {})),
                        network_config=NetworkConfig(**data.get("network_config", {})),
                        environment=data.get("environment", {}),
                        metadata=data.get("metadata", {}),
                        persistent_storage=data.get("persistent_storage", False),
                        persistent_path=Path(data["persistent_path"])
                        if data.get("persistent_path")
                        else None,
                    )

                    self._active_sandboxes[sandbox.name] = sandbox
                    self._sandbox_locks[sandbox.name] = asyncio.Lock()
                    logger.info(f"Loaded existing sandbox: {sandbox.name}")

                except Exception as e:
                    logger.error(f"Error loading sandbox from {entry}: {e}")

    def _save_sandbox_state(self, sandbox: SandboxInfo):
        """Save sandbox state to disk."""
        if not sandbox.persistent_storage:
            return

        state_file = sandbox.directory / "sandbox.json"
        state_data = {
            "name": sandbox.name,
            "sandbox_type": sandbox.sandbox_type.value,
            "state": sandbox.state.value,
            "created_at": sandbox.created_at.isoformat(),
            "last_used": sandbox.last_used.isoformat() if sandbox.last_used else None,
            "resource_limits": sandbox.resource_limits.dict(),
            "network_config": sandbox.network_config.dict(),
            "environment": sandbox.environment,
            "metadata": sandbox.metadata,
            "persistent_storage": sandbox.persistent_storage,
            "persistent_path": str(sandbox.persistent_path) if sandbox.persistent_path else None,
        }

        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2, default=str)

    async def create_sandbox(
        self,
        name: str,
        sandbox_type: SandboxType | str = SandboxType.VENV,
        requirements: list[str] | None = None,
        environment: dict[str, str] | None = None,
        resource_limits: dict | ResourceLimits | None = None,
        network_config: dict | NetworkConfig | None = None,
        persistent_storage: bool = False,
        timeout: int = 300,
        **kwargs,
    ) -> SandboxInfo:
        """Create a new sandbox environment with advanced configuration.

        Args:
            name: Unique name for the sandbox
            sandbox_type: Type of sandbox to create (venv, docker, windows_sandbox)
            requirements: List of Python packages to install
            environment: Environment variables to set in the sandbox
            resource_limits: Resource limits for the sandbox
            network_config: Network configuration for the sandbox
            persistent_storage: Whether to persist the sandbox between sessions
            timeout: Timeout in seconds for sandbox operations
            **kwargs: Additional sandbox-specific parameters

        Returns:
            SandboxInfo object with sandbox details

        Raises:
            ValueError: If sandbox with this name already exists or invalid parameters
            RuntimeError: If sandbox creation fails
        """
        if not name.replace("_", "").isalnum():
            raise ValueError(
                "Sandbox name must contain only alphanumeric characters and underscores"
            )

        if name in self._active_sandboxes:
            raise ValueError(f"Sandbox '{name}' already exists")

        # Convert string sandbox_type to enum if needed
        if isinstance(sandbox_type, str):
            sandbox_type = SandboxType(sandbox_type.lower())

        # Create sandbox directory
        sandbox_dir = self.base_dir / name
        persistent_path = None

        if persistent_storage:
            persistent_path = sandbox_dir / "persistent"
            persistent_path.mkdir(parents=True, exist_ok=True)

        # Create sandbox info
        sandbox = SandboxInfo(
            name=name,
            sandbox_type=sandbox_type,
            directory=sandbox_dir,
            environment=environment or {},
            resource_limits=ResourceLimits(**(resource_limits or {})),
            network_config=NetworkConfig(**(network_config or {})),
            persistent_storage=persistent_storage,
            persistent_path=persistent_path,
            metadata=kwargs.get("metadata", {}),
        )

        # Create a lock for this sandbox
        self._sandbox_locks[name] = asyncio.Lock()

        async with self._sandbox_locks[name]:
            try:
                sandbox.state = SandboxState.CREATING

                # Create the sandbox based on type
                if sandbox_type == SandboxType.VENV:
                    await self._create_venv(sandbox, requirements, timeout)
                elif sandbox_type == SandboxType.DOCKER:
                    await self._create_docker_container(sandbox, requirements, timeout)
                elif sandbox_type == SandboxType.WINDOWS_SANDBOX and self.platform == "windows":
                    await self._create_windows_sandbox(sandbox, requirements, timeout)
                else:
                    raise ValueError(f"Unsupported sandbox type: {sandbox_type}")

                sandbox.state = SandboxState.READY
                sandbox.last_used = datetime.utcnow()
                self._active_sandboxes[name] = sandbox

                # Save initial state
                self._save_sandbox_state(sandbox)

                logger.info(f"Created sandbox '{name}' of type {sandbox_type}")
                return sandbox

            except Exception as e:
                sandbox.state = SandboxState.ERROR
                logger.error(f"Failed to create sandbox '{name}': {e}", exc_info=True)

                # Clean up on failure
                try:
                    if sandbox_dir.exists() and not persistent_storage:
                        shutil.rmtree(sandbox_dir)
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up failed sandbox: {cleanup_error}")

                if name in self._active_sandboxes:
                    del self._active_sandboxes[name]

                raise RuntimeError(f"Failed to create sandbox '{name}': {e}") from e

    async def run_in_sandbox(
        self,
        sandbox_name: str,
        command: str | list[str],
        files: dict[str, str | bytes] | None = None,
        capture_output: bool = True,
        timeout: int = 300,
        working_dir: str | None = None,
        environment: dict[str, str] | None = None,
        check_resources: bool = True,
        **kwargs,
    ) -> TestResult:
        """Run a command in the specified sandbox with advanced options.

        Args:
            sandbox_name: Name of the sandbox to use
            command: Command to execute (can be a string or list of args)
            files: Dictionary of {filename: content} to create in the sandbox
            capture_output: Whether to capture and return command output
            timeout: Timeout in seconds
            working_dir: Working directory inside the sandbox
            environment: Additional environment variables
            check_resources: Whether to check resource limits before running
            **kwargs: Additional arguments for the command

        Returns:
            TestResult with the command results and resource usage

        Raises:
            ValueError: If sandbox is not found or invalid parameters
            RuntimeError: If command execution fails
        """
        if sandbox_name not in self._active_sandboxes:
            raise ValueError(f"Sandbox '{sandbox_name}' not found")

        sandbox = self._active_sandboxes[sandbox_name]

        # Check if sandbox is ready
        if sandbox.state != SandboxState.READY:
            raise RuntimeError(f"Sandbox '{sandbox_name}' is not ready (state: {sandbox.state})")

        # Check resource limits
        if check_resources and not await self._check_resource_limits(sandbox):
            raise RuntimeError("Resource limits exceeded")

        # Prepare files in the sandbox
        file_paths = []
        if files:
            for filename, content in files.items():
                file_path = sandbox.directory / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)

                if isinstance(content, bytes):
                    file_path.write_bytes(content)
                else:
                    file_path.write_text(str(content), encoding="utf-8")
                file_paths.append(file_path)

        # Update environment
        env = {**sandbox.environment, **(environment or {})}

        # Execute the command with the sandbox lock
        async with self._sandbox_locks[sandbox_name]:
            sandbox.state = SandboxState.RUNNING
            start_time = asyncio.get_event_loop().time()
            result = TestResult(
                success=False,
                output="",
                sandbox_type=sandbox.sandbox_type,
                files_generated=[],
                resource_usage=sandbox.resource_usage,
            )

            try:
                # Run the command based on sandbox type
                if sandbox.sandbox_type == SandboxType.VENV:
                    cmd_result = await self._run_in_venv(
                        sandbox,
                        command,
                        capture_output,
                        timeout,
                        working_dir=working_dir,
                        environment=env,
                        **kwargs,
                    )
                elif sandbox.sandbox_type == SandboxType.DOCKER:
                    cmd_result = await self._run_in_docker(
                        sandbox,
                        command,
                        capture_output,
                        timeout,
                        working_dir=working_dir,
                        environment=env,
                        **kwargs,
                    )
                elif (
                    sandbox.sandbox_type == SandboxType.WINDOWS_SANDBOX
                    and self.platform == "windows"
                ):
                    cmd_result = await self._run_in_windows_sandbox(
                        sandbox,
                        command,
                        capture_output,
                        timeout,
                        working_dir=working_dir,
                        environment=env,
                        **kwargs,
                    )
                else:
                    raise ValueError(f"Unsupported sandbox type: {sandbox.sandbox_type}")

                # Update result
                result.success = cmd_result.returncode == 0
                result.output = cmd_result.stdout or ""
                result.error = cmd_result.stderr if cmd_result.returncode != 0 else None
                result.execution_time = asyncio.get_event_loop().time() - start_time
                result.exit_code = cmd_result.returncode

                # Check for resource overages
                if await self._check_resource_overages(sandbox):
                    result.warnings.append(
                        "Resource limits approached or exceeded during execution"
                    )

                return result

            except asyncio.TimeoutError:
                result.error = f"Command timed out after {timeout} seconds"
                result.execution_time = timeout
                return result

            except Exception as e:
                result.error = str(e)
                result.execution_time = asyncio.get_event_loop().time() - start_time
                return result

            finally:
                # Clean up temporary files
                for file_path in file_paths:
                    try:
                        if file_path.exists():
                            file_path.unlink()
                    except Exception as e:
                        logger.warning(f"Error cleaning up file {file_path}: {e}")

                # Update sandbox state
                sandbox.state = SandboxState.READY
                sandbox.last_used = datetime.utcnow()
                self._save_sandbox_state(sandbox)

    async def cleanup_sandbox(self, name: str, force: bool = False) -> bool:
        """Clean up a sandbox environment.

        Args:
            name: Name of the sandbox to clean up
            force: If True, force cleanup even if sandbox is running

        Returns:
            True if cleanup was successful, False otherwise

        Raises:
            ValueError: If sandbox doesn't exist
            RuntimeError: If sandbox is running and force=False
        """
        if name not in self._active_sandboxes and name not in [
            d.name for d in self.base_dir.iterdir() if d.is_dir()
        ]:
            raise ValueError(f"Sandbox '{name}' not found")

        sandbox = self._active_sandboxes.get(name)

        # If sandbox is running and force=False, raise an error
        if sandbox and sandbox.state == SandboxState.RUNNING and not force:
            raise RuntimeError(
                f"Cannot clean up running sandbox '{name}'. Stop it first or use force=True"
            )

        async with self._sandbox_locks.get(name, asyncio.Lock()):
            try:
                # If sandbox is running and force=True, stop it first
                if sandbox and sandbox.state == SandboxState.RUNNING and force:
                    await self._stop_sandbox_process(sandbox)

                # Remove sandbox directory if it exists
                sandbox_dir = self.base_dir / name
                if sandbox_dir.exists():
                    if sandbox and sandbox.persistent_storage and not force:
                        logger.info(
                            f"Skipping removal of persistent sandbox '{name}'. Use force=True to remove."
                        )
                        return False

                    shutil.rmtree(sandbox_dir, ignore_errors=True)

                # Clean up references
                if name in self._active_sandboxes:
                    del self._active_sandboxes[name]
                if name in self._sandbox_locks:
                    del self._sandbox_locks[name]

                logger.info(f"Cleaned up sandbox: {name}")
                return True

            except Exception as e:
                logger.error(f"Error cleaning up sandbox '{name}': {e}", exc_info=True)
                return False

    async def _stop_sandbox_process(self, sandbox: SandboxInfo) -> bool:
        """Stop a running sandbox process.

        Args:
            sandbox: The sandbox to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        if not sandbox.process or sandbox.process.returncode is not None:
            return True

        try:
            # Try to terminate gracefully first
            sandbox.process.terminate()
            try:
                await asyncio.wait_for(sandbox.process.wait(), timeout=5)
                return True
            except asyncio.TimeoutError:
                # Force kill if it doesn't terminate
                sandbox.process.kill()
                await sandbox.process.wait()
                return True
        except Exception as e:
            logger.warning(f"Error stopping sandbox process: {e}")
            return False

    async def _check_resource_limits(self, sandbox: SandboxInfo) -> bool:
        """Check if resource usage is within limits.

        Args:
            sandbox: The sandbox to check

        Returns:
            True if within limits, False otherwise
        """
        if not sandbox.resource_limits:
            return True

        usage = sandbox.resource_usage
        limits = sandbox.resource_limits

        if limits.max_cpu_percent and usage.cpu_percent > limits.max_cpu_percent:
            logger.warning(
                f"CPU usage {usage.cpu_percent}% exceeds limit of {limits.max_cpu_percent}%"
            )
            return False

        if limits.max_memory_mb and usage.memory_mb > limits.max_memory_mb:
            logger.warning(
                f"Memory usage {usage.memory_mb}MB exceeds limit of {limits.max_memory_mb}MB"
            )
            return False

        if limits.max_disk_mb and (usage.disk_read_mb + usage.disk_write_mb) > limits.max_disk_mb:
            logger.warning(
                f"Disk I/O {usage.disk_read_mb + usage.disk_write_mb}MB exceeds limit of {limits.max_disk_mb}MB"
            )
            return False

        return True

    async def _check_resource_overages(self, sandbox: SandboxInfo) -> bool:
        """Check if resource usage is approaching or exceeding limits.

        Args:
            sandbox: The sandbox to check

        Returns:
            True if approaching or exceeding limits, False otherwise
        """
        if not sandbox.resource_limits:
            return False

        usage = sandbox.resource_usage
        limits = sandbox.resource_limits
        warnings = []

        if limits.max_cpu_percent and usage.cpu_percent > (limits.max_cpu_percent * 0.8):
            warnings.append(f"CPU usage at {usage.cpu_percent}% (limit: {limits.max_cpu_percent}%)")

        if limits.max_memory_mb and usage.memory_mb > (limits.max_memory_mb * 0.8):
            warnings.append(
                f"Memory usage at {usage.memory_mb:.1f}MB (limit: {limits.max_memory_mb}MB)"
            )

        if limits.max_disk_mb and (usage.disk_read_mb + usage.disk_write_mb) > (
            limits.max_disk_mb * 0.8
        ):
            total = usage.disk_read_mb + usage.disk_write_mb
            warnings.append(f"Disk I/O at {total:.1f}MB (limit: {limits.max_disk_mb}MB)")

        if warnings:
            logger.warning("Resource usage warnings:\n" + "\n".join(warnings))
            return True

        return False

    # Implementation methods for different sandbox types

    async def _create_venv(
        self, venv_dir: Path, requirements: list[str] | None, timeout: int
    ) -> None:
        """Create a Python virtual environment."""
        # Create the virtual environment
        await self._run_command(["python", "-m", "venv", str(venv_dir)], timeout=timeout)

        # Install requirements if specified
        if requirements:
            pip_path = (
                venv_dir / "Scripts" / "pip"
                if self.platform == "windows"
                else venv_dir / "bin" / "pip"
            )
            await self._run_command([str(pip_path), "install"] + requirements, timeout=timeout)

    async def _run_in_venv(
        self, venv_dir: Path, command: str, capture_output: bool, timeout: int
    ) -> subprocess.CompletedProcess:
        """Run a command in a virtual environment."""
        python_path = (
            venv_dir / "Scripts" / "python"
            if self.platform == "windows"
            else venv_dir / "bin" / "python"
        )
        return await self._run_command([str(python_path), "-c", command], capture_output, timeout)

    async def _create_docker_container(
        self, container_dir: Path, requirements: list[str] | None, timeout: int
    ) -> None:
        """Create a Docker container for testing."""
        # This is a simplified example - in a real implementation, you would:
        # 1. Create a Dockerfile with the required setup
        # 2. Build the Docker image
        # 3. Start the container
        raise NotImplementedError("Docker sandbox not yet implemented")

    async def _run_in_docker(
        self, container_name: str, host_dir: Path, command: str, capture_output: bool, timeout: int
    ) -> subprocess.CompletedProcess:
        """Run a command in a Docker container."""
        # This would run a command in an existing container
        raise NotImplementedError("Docker sandbox not yet implemented")

    async def _stop_docker_container(self, container_name: str) -> None:
        """Stop and remove a Docker container."""
        # This would stop and remove a container
        pass

    async def _create_windows_sandbox(
        self, sandbox_dir: Path, requirements: list[str] | None, timeout: int
    ) -> None:
        """Set up a Windows Sandbox environment."""
        if self.platform != "windows":
            raise RuntimeError("Windows Sandbox is only available on Windows")

        # This would set up a Windows Sandbox configuration
        # For now, we'll just create a basic setup script
        setup_script = sandbox_dir / "setup.ps1"
        setup_content = [
            "# Windows Sandbox setup script",
            "Write-Host 'Setting up Windows Sandbox environment...'",
        ]

        if requirements:
            setup_content.extend(
                ["# Install Python packages", f"pip install {' '.join(requirements)}"]
            )

        setup_script.write_text("\n".join(setup_content), encoding="utf-8")

    async def _run_in_windows_sandbox(
        self, sandbox_dir: Path, command: str, capture_output: bool, timeout: int
    ) -> subprocess.CompletedProcess:
        """Run a command in Windows Sandbox."""
        if self.platform != "windows":
            raise RuntimeError("Windows Sandbox is only available on Windows")

        # This would run a command in Windows Sandbox
        # For now, we'll just run it locally as a fallback
        return await self._run_command(["powershell", "-Command", command], capture_output, timeout)

    async def _run_command(
        self, command: list[str], capture_output: bool = True, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """Run a shell command with asyncio."""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            text=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return subprocess.CompletedProcess(
                args=command, returncode=process.returncode, stdout=stdout, stderr=stderr
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")


# Create a singleton instance
sandbox_tester = SandboxTester()

# Initialize the sandbox tester when the module is imported
# but don't start any tasks until initialize() is called

# Public API functions


async def create_sandbox(
    name: str,
    sandbox_type: str = "venv",
    requirements: list[str] | None = None,
    environment: dict[str, str] | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    """Create a new sandbox environment.

    Args:
        name: Unique name for the sandbox
        sandbox_type: Type of sandbox to create (venv, docker, windows_sandbox)
        requirements: List of Python packages to install
        environment: Environment variables to set in the sandbox
        timeout: Timeout in seconds for sandbox operations

    Returns:
        Dictionary with sandbox information
    """
    return await sandbox_tester.create_sandbox(
        name=name,
        sandbox_type=SandboxType(sandbox_type.lower()),
        requirements=requirements or [],
        environment=environment or {},
        timeout=timeout,
    )


async def run_in_sandbox(
    sandbox_name: str,
    command: str,
    files: dict[str, str] | None = None,
    capture_output: bool = True,
    timeout: int = 300,
) -> TestResult:
    """Run a command in the specified sandbox.

    Args:
        sandbox_name: Name of the sandbox to use
        command: Command to execute
        files: Dictionary of {filename: content} to create in the sandbox
        capture_output: Whether to capture and return command output
        timeout: Timeout in seconds

    Returns:
        TestResult with the command results
    """
    return await sandbox_tester.run_in_sandbox(
        sandbox_name=sandbox_name,
        command=command,
        files=files or {},
        capture_output=capture_output,
        timeout=timeout,
    )


async def cleanup_sandbox(name: str) -> bool:
    """Clean up a sandbox environment.

    Args:
        name: Name of the sandbox to clean up

    Returns:
        True if cleanup was successful, False otherwise
    """
    return await sandbox_tester.cleanup_sandbox(name)
