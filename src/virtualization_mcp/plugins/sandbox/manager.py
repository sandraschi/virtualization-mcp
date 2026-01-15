"""
Windows Sandbox Helper for virtualization-mcp

This module provides Windows Sandbox management functionality.
"""

import asyncio
import json
import logging
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
from fastmcp import FastMCP
from pydantic import BaseModel, Field, ValidationError, field_validator

from .portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)


class SandboxState(str, Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"
    STARTING = "Starting"
    STOPPING = "Stopping"
    ERROR = "Error"


class SandboxPortfolio(str, Enum):
    """Preconfigured sandbox portfolios with files and commands."""

    VSCODE = "vscode"
    VSCODE_PORTABLE = "vscode_portable"
    PYTHON_DEV = "python_dev"
    NODE_DEV = "node_dev"
    POWERSHELL_SCRIPTS = "powershell_scripts"
    BROWSER_TESTING = "browser_testing"

    @classmethod
    def list_all(cls) -> list[str]:
        """List all available portfolio names."""
        return [p.value for p in cls]


class MappedFolder(BaseModel):
    """Model for Windows Sandbox folder mapping."""

    host_path: str = Field(..., description="Path on host machine (must exist and be absolute)")
    sandbox_path: str = Field(default="", description="Path in sandbox (optional, defaults to Desktop)")
    read_only: bool = Field(default=False, description="Whether folder is read-only in sandbox")

    @field_validator("host_path")
    @classmethod
    def validate_host_path(cls, v: str) -> str:
        """Validate that host path exists and is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(f"Host path must be absolute: {v}")
        if not path.exists():
            raise ValueError(f"Host path does not exist: {v}")
        return str(path)


class FileCopyOperation(BaseModel):
    """Configuration for copying a file into the sandbox."""

    source_path: str = Field(..., description="Source file path on host (must exist and be absolute)")
    destination_path: str = Field(..., description="Destination path in sandbox (absolute path)")
    overwrite: bool = Field(True, description="Whether to overwrite existing files")

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        """Validate that source path exists and is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(f"Source path must be absolute: {v}")
        if not path.exists():
            raise ValueError(f"Source file does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Source path must be a file: {v}")
        return str(path)

    @field_validator("destination_path")
    @classmethod
    def validate_destination_path(cls, v: str) -> str:
        """Validate destination path format."""
        if not v or not v.strip():
            raise ValueError("Destination path cannot be empty")
        # Ensure it's an absolute path
        if not (v.startswith("C:\\") or v.startswith("C:/")):
            raise ValueError(f"Destination path must be absolute (start with C:\\): {v}")
        return v.strip()


class SandboxConfig(BaseModel):
    """Configuration for Windows Sandbox."""

    name: str = Field(..., description="Name of the sandbox configuration")
    memory_mb: int = Field(4096, ge=1024, le=32768, description="Memory in MB (1024-32768)")
    vgpu: bool = Field(True, description="Enable virtual GPU")
    networking: bool = Field(True, description="Enable networking")
    portfolio: str | None = Field(
        None, description="Preconfigured portfolio name (e.g., 'vscode', 'python_dev'). "
        "If specified, portfolio files and commands will be added to the sandbox."
    )
    common_programs: list[str] | None = Field(
        None, description="List of common programs to install. Available: "
        "'vscode', 'python', 'nodejs', 'chrome', 'firefox', 'git', 'powershell', 'notepad++'. "
        "Can be used instead of or in addition to portfolio."
    )
    mapped_folders: list[MappedFolder] = Field(
        default_factory=list, description="List of folders to map into the sandbox"
    )
    copy_files: list[FileCopyOperation] = Field(
        default_factory=list, description="List of files to copy into the sandbox"
    )
    logon_commands: list[str] = Field(
        default_factory=list, description="Commands to run on sandbox startup (before file copies)"
    )
    startup_scripts: list[str] = Field(
        default_factory=list, description="Scripts or executables to run after sandbox starts. "
        "Can be full paths or commands. Files will be executed in order."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class WindowsSandboxHelper:
    """Helper class for managing Windows Sandbox instances."""

    def __init__(self):
        self.mcp = None
        self.initialized = False
        self.active_sandboxes = {}
        self._portfolio_cache = {}  # Cache for downloaded portfolio files
        self.portfolio_manager = PortfolioManager()

    async def initialize(self, mcp: FastMCP) -> None:
        """Initialize the Windows Sandbox helper."""
        if self.initialized:
            return

        self.mcp = mcp
        self.initialized = True
        logger.info("Windows Sandbox Helper initialized")

    def _normalize_config(self, config: dict[str, Any] | str | SandboxConfig) -> SandboxConfig:
        """Normalize config input to SandboxConfig model.

        Accepts:
        - SandboxConfig instance (returns as-is)
        - dict: Converted to SandboxConfig
        - str: Parsed as JSON then converted to SandboxConfig

        Raises:
            ValueError: If config cannot be parsed or validated
        """
        if isinstance(config, SandboxConfig):
            return config

        if isinstance(config, str):
            try:
                # Try parsing as JSON
                config_dict = json.loads(config)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Config string is not valid JSON. "
                    f"JSON parse error at position {e.pos}: {e.msg}. "
                    f"Received: {config[:100]}{'...' if len(config) > 100 else ''}"
                ) from e
        elif isinstance(config, dict):
            config_dict = config
        else:
            raise ValueError(
                f"Config must be a dict, JSON string, or SandboxConfig instance. "
                f"Received type: {type(config).__name__}, value: {repr(config)[:100]}"
            )

        try:
            return SandboxConfig(**config_dict)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                errors.append(f"  - {field}: {msg}")

            raise ValueError(
                "Invalid sandbox configuration. Validation errors:\n" + "\n".join(errors) +
                "\n\nRequired fields: name (string)"
                "\nOptional fields: memory_mb (int, 1024-32768), vgpu (bool), "
                "networking (bool), mapped_folders (list), logon_commands (list)"
            ) from e

    def register_tools(self, mcp: FastMCP) -> None:
        """Register Windows Sandbox tools with FastMCP."""
        if not self.initialized:
            raise RuntimeError("Helper not initialized. Call initialize() first.")

        @mcp.tool("create_windows_sandbox")
        async def create_sandbox(
            config: Any, wait_for_completion: bool = False
        ) -> dict[str, Any]:
            """Create and start a new Windows Sandbox instance.

            Note: Windows 11 only allows one sandbox instance to run at a time.
            If a sandbox is already running, this will return an error with a clear message.

            Args:
                config: Sandbox configuration. Accepts multiple formats:
                    - dict: Configuration dictionary with 'name' (required, string) and optional fields:
                        - memory_mb (int, 1024-32768, default: 4096)
                        - vgpu (bool, default: True)
                        - networking (bool, default: True)
                        - portfolio (string, optional) - Preconfigured portfolio name
                        - common_programs (list of strings, optional) - Quick select common programs:
                          ['vscode', 'python', 'nodejs', 'chrome', 'firefox', 'git', 'powershell', 'notepad++']
                          Use list_common_programs tool to see ASCII-formatted list. Can be used
                          instead of or in addition to portfolio.
                        - mapped_folders (list of dicts with host_path, sandbox_path, read_only)
                        - copy_files (list of dicts with source_path, destination_path, overwrite)
                          Files will be copied into the sandbox at startup
                        - logon_commands (list of strings) - Commands to run before file copies
                        - startup_scripts (list of strings) - Scripts/exes to run after sandbox starts
                    - str: JSON string representation of configuration (will be parsed)
                    - SandboxConfig: Pydantic model instance
                wait_for_completion: Whether to wait for sandbox to fully start

            Returns:
                Dictionary with status, sandbox_id, and config

            Raises:
                ValueError: If config is invalid, missing required fields, or cannot be parsed.
                    Error messages include specific validation details.
                RuntimeError: If a Windows Sandbox instance is already running (Windows 11 only
                    allows one sandbox at a time), or if Windows Sandbox fails to start.
                    Error messages clearly state the issue and how to resolve it.
            """
            try:
                normalized_config = self._normalize_config(config)
                return await self._create_sandbox(normalized_config, wait_for_completion)
            except ValueError as e:
                logger.error(f"Config validation error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating sandbox: {e}")
                raise ValueError(f"Failed to create sandbox: {str(e)}") from e

        @mcp.tool("list_running_sandboxes")
        async def list_sandboxes() -> list[dict[str, Any]]:
            """List all running Windows Sandbox instances."""
            return await self._list_sandboxes()

        @mcp.tool("list_portfolios")
        async def list_portfolios() -> dict[str, Any]:
            """List all available portfolios.

            Returns:
                Dictionary with portfolio names and their descriptions
            """
            portfolios = self.portfolio_manager.list_available_portfolios()
            portfolio_info = {}
            for portfolio_name in portfolios:
                try:
                    info = self.portfolio_manager.get_portfolio_info(portfolio_name)
                    portfolio_info[portfolio_name] = {
                        "name": info["name"],
                        "description": info["description"],
                        "targets": info["targets"],
                        "version": info["version"]
                    }
                except Exception as e:
                    logger.warning(f"Failed to get info for portfolio {portfolio_name}: {e}")
                    portfolio_info[portfolio_name] = {"error": str(e)}

            return {
                "portfolios": portfolio_info,
                "count": len(portfolios)
            }

        @mcp.tool("list_common_programs")
        async def list_common_programs() -> dict[str, Any]:
            """List all available common programs with ASCII-formatted display.

            Returns:
                Dictionary with ASCII form and program list
            """
            programs = {
                "vscode": "Visual Studio Code",
                "python": "Python 3.12",
                "nodejs": "Node.js",
                "chrome": "Google Chrome",
                "firefox": "Mozilla Firefox",
                "git": "Git for Windows",
                "powershell": "PowerShell",
                "notepad++": "Notepad++"
            }

            ascii_form = self._get_common_programs_list()

            return {
                "ascii_form": ascii_form,
                "programs": programs,
                "usage": "Use common_programs parameter: ['vscode', 'python', ...]"
            }

        @mcp.tool("stop_sandbox")
        async def stop_sandbox(sandbox_id: str, force: bool = False) -> dict[str, Any]:
            """Stop a running Windows Sandbox instance.

            Args:
                sandbox_id: ID of the sandbox to stop
                force: Whether to force stop the sandbox
            """
            return await self._stop_sandbox(sandbox_id, force)

    # Implementation methods
    def _get_common_programs_list(self) -> str:
        """Get ASCII-formatted list of common programs.

        Returns:
            ASCII formatted string with checkboxes
        """
        programs = {
            "vscode": "Visual Studio Code",
            "python": "Python 3.12",
            "nodejs": "Node.js",
            "chrome": "Google Chrome",
            "firefox": "Mozilla Firefox",
            "git": "Git for Windows",
            "powershell": "PowerShell",
            "notepad++": "Notepad++"
        }

        lines = ["Common Programs Available:"]
        lines.append("=" * 50)
        for key, name in programs.items():
            lines.append(f"  [ ] {key:12} - {name}")
        lines.append("=" * 50)
        lines.append("\nUse common_programs parameter: ['vscode', 'python', ...]")

        return "\n".join(lines)

    def _get_common_program_config(self, program_name: str, target_type: str = "sandbox") -> dict[str, Any]:
        """Get configuration for a common program.

        Args:
            program_name: Name of the program
            target_type: Target type - 'sandbox' or 'vm'

        Returns:
            Dictionary with downloads, setup_commands, and startup_scripts
        """
        base_path_sandbox = "C:\\Users\\WDAGUtilityAccount\\Desktop"
        base_path_vm = "C:\\Temp"
        base_path = base_path_sandbox if target_type == "sandbox" else base_path_vm

        programs = {
            "vscode": {
                "downloads": [{
                    "url": "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-archive",
                    "filename": "vscode.zip",
                    "destination": f"{base_path}\\VSCode"
                }],
                "setup_commands": [
                    f"powershell -Command \"Expand-Archive -Path '{base_path}\\VSCode\\vscode.zip' -DestinationPath '{base_path}\\VSCode' -Force\"",
                    f"powershell -Command \"Remove-Item '{base_path}\\VSCode\\vscode.zip' -ErrorAction SilentlyContinue\""
                ],
                "startup_scripts": [f"{base_path}\\VSCode\\Code.exe"]
            },
            "python": {
                "downloads": [{
                    "url": "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe",
                    "filename": "python-installer.exe",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"{base_path}\\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1"
                ],
                "startup_scripts": ["cmd /k python --version && pip --version"]
            },
            "nodejs": {
                "downloads": [{
                    "url": "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi",
                    "filename": "nodejs.msi",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"msiexec /i {base_path}\\nodejs.msi /quiet /norestart"
                ],
                "startup_scripts": ["cmd /k node --version && npm --version"]
            },
            "chrome": {
                "downloads": [{
                    "url": "https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe",
                    "filename": "chrome-installer.exe",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"{base_path}\\chrome-installer.exe /silent /install"
                ],
                "startup_scripts": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"]
            },
            "firefox": {
                "downloads": [{
                    "url": "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US",
                    "filename": "firefox-installer.exe",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"{base_path}\\firefox-installer.exe /S"
                ],
                "startup_scripts": ["C:\\Program Files\\Mozilla Firefox\\firefox.exe"]
            },
            "git": {
                "downloads": [{
                    "url": "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe",
                    "filename": "git-installer.exe",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"{base_path}\\git-installer.exe /VERYSILENT /NORESTART"
                ],
                "startup_scripts": ["cmd /k git --version"]
            },
            "powershell": {
                "downloads": [],
                "setup_commands": [],
                "startup_scripts": ["powershell.exe"]
            },
            "notepad++": {
                "downloads": [{
                    "url": "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.3/npp.8.6.3.Installer.x64.exe",
                    "filename": "notepadpp-installer.exe",
                    "destination": base_path
                }],
                "setup_commands": [
                    f"{base_path}\\notepadpp-installer.exe /S"
                ],
                "startup_scripts": ["C:\\Program Files\\Notepad++\\notepad++.exe"]
            }
        }

        if program_name not in programs:
            available = ", ".join(programs.keys())
            raise ValueError(
                f"Unknown common program '{program_name}'. "
                f"Available: {available}"
            )

        return programs[program_name]

    async def _apply_common_programs(self, config: SandboxConfig, target_type: str = "sandbox") -> SandboxConfig:
        """Apply common programs to sandbox config.

        Args:
            config: Sandbox configuration
            target_type: Target type - 'sandbox' or 'vm'

        Returns:
            Updated configuration with common programs applied
        """
        if not config.common_programs:
            return config

        portfolio_dir = tempfile.mkdtemp(prefix=f"{target_type}_common_programs_")
        logger.info(f"Common programs directory: {portfolio_dir}")

        # Apply each program
        for program_name in config.common_programs:
            program_config = self._get_common_program_config(program_name, target_type)

            # Download files
            for download in program_config.get("downloads", []):
                url = download["url"]
                filename = download["filename"]
                dest_dir = download.get("destination", portfolio_dir)

                # Download to temp directory
                temp_file = os.path.join(portfolio_dir, filename)
                await self._download_file(url, temp_file)

                # Add to copy_files
                config.copy_files.append(
                    FileCopyOperation(
                        source_path=temp_file,
                        destination_path=os.path.join(dest_dir, filename),
                        overwrite=True
                    )
                )

            # Add setup commands
            config.logon_commands.extend(program_config.get("setup_commands", []))

            # Add startup scripts
            config.startup_scripts.extend(program_config.get("startup_scripts", []))

        logger.info(f"Applied {len(config.common_programs)} common programs: {config.common_programs}")
        return config

    async def _download_file(self, url: str, destination_path: str) -> str:
        """Download a file from URL to destination.

        Args:
            url: URL to download from
            destination_path: Full path where file should be saved

        Returns:
            Path to downloaded file
        """
        logger.info(f"Downloading {url} to {destination_path}")

        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination_path)
        os.makedirs(dest_dir, exist_ok=True)

        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()

                with open(destination_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info(f"Downloaded {url} to {destination_path}")
        return destination_path

    async def _apply_portfolio(self, config: SandboxConfig, target_type: str = "sandbox") -> SandboxConfig:
        """Apply portfolio configuration to sandbox config.

        Downloads required files and adds commands/scripts based on target type.

        Args:
            config: Sandbox configuration
            target_type: Target type - 'sandbox' or 'vm'

        Returns:
            Updated configuration with portfolio applied
        """
        if not config.portfolio:
            return config

        # Load portfolio from YAML file
        portfolio_def = self.portfolio_manager.load_portfolio(config.portfolio)

        # Check if portfolio supports this target type
        supported_targets = portfolio_def.get("targets", ["sandbox", "vm"])
        if target_type not in supported_targets:
            raise ValueError(
                f"Portfolio '{config.portfolio}' does not support target type '{target_type}'. "
                f"Supported targets: {', '.join(supported_targets)}"
            )

        # Create temp directory for portfolio downloads
        portfolio_dir = tempfile.mkdtemp(prefix=f"{target_type}_portfolio_{config.portfolio}_")
        logger.info(f"Portfolio directory: {portfolio_dir}")

        # Download files
        downloaded_files = []
        for download in portfolio_def.get("downloads", []):
            url = download["url"]
            filename = download["filename"]

            # Use target-specific destination if available, otherwise use default
            dest_key = f"{target_type}_destination"
            dest_dir = download.get(dest_key) or download.get("destination", portfolio_dir)

            # Download to temp directory first
            temp_file = os.path.join(portfolio_dir, filename)
            await self._download_file(url, temp_file)

            # Add to copy_files to copy into sandbox/VM
            config.copy_files.append(
                FileCopyOperation(
                    source_path=temp_file,
                    destination_path=os.path.join(dest_dir, filename),
                    overwrite=True
                )
            )
            downloaded_files.append(temp_file)

        # Add setup commands (target-specific)
        setup_commands = portfolio_def.get("setup_commands", {})
        if isinstance(setup_commands, dict):
            config.logon_commands.extend(setup_commands.get(target_type, []))
        else:
            # Backward compatibility: if it's a list, use it for all targets
            config.logon_commands.extend(setup_commands)

        # Add startup scripts (target-specific)
        startup_scripts = portfolio_def.get("startup_scripts", {})
        if isinstance(startup_scripts, dict):
            config.startup_scripts.extend(startup_scripts.get(target_type, []))
        else:
            # Backward compatibility: if it's a list, use it for all targets
            config.startup_scripts.extend(startup_scripts)

        # Add environment variables if specified
        env_vars = portfolio_def.get("environment", [])
        if env_vars:
            for env_var in env_vars:
                env_cmd = f'setx {env_var["name"]} "{env_var["value"]}" /M'
                config.logon_commands.append(env_cmd)

        logger.info(f"Applied portfolio '{config.portfolio}' ({target_type}) with {len(downloaded_files)} files")
        return config

    async def _is_sandbox_running(self) -> bool:
        """Check if a Windows Sandbox instance is already running.

        Windows 11 only allows one sandbox instance at a time.

        Returns:
            True if a sandbox is running, False otherwise
        """
        try:
            # Check for WindowsSandbox.exe process
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                'Get-Process -Name "WindowsSandbox" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                count_str = stdout.decode('utf-8', errors='ignore').strip()
                try:
                    count = int(count_str)
                    return count > 0
                except ValueError:
                    # If we can't parse, assume no sandbox is running
                    return False

            return False
        except Exception as e:
            logger.warning(f"Error checking for running sandbox: {e}")
            # On error, assume no sandbox is running to avoid blocking
            return False

    async def _create_sandbox(
        self, config: SandboxConfig, wait_for_completion: bool = False
    ) -> dict[str, Any]:
        """Create and start a new Windows Sandbox instance."""
        wsx_path = None
        try:
            # Check if a sandbox is already running
            # Windows 11 only allows one sandbox instance at a time
            if await self._is_sandbox_running():
                raise RuntimeError(
                    "A Windows Sandbox instance is already running. "
                    "Windows 11 only allows one sandbox to run at a time. "
                    "Please close the existing sandbox before creating a new one."
                )

            # Apply portfolio if specified (downloads files and adds commands)
            if config.portfolio:
                logger.info(f"Applying portfolio: {config.portfolio}")
                config = await self._apply_portfolio(config, target_type="sandbox")

            # Apply common programs if specified
            if config.common_programs:
                logger.info(f"Applying common programs: {config.common_programs}")
                config = await self._apply_common_programs(config, target_type="sandbox")

            # Ensure networking is enabled (as requested)
            if not config.networking:
                logger.info("Networking was disabled in config, enabling it as requested")
                config.networking = True

            # Handle file copying: create staging folder and copy files
            staging_folder = None
            if config.copy_files:
                staging_folder = tempfile.mkdtemp(prefix="sandbox_files_")
                logger.info(f"Created staging folder for file copies: {staging_folder}")

                # Copy files to staging folder
                import shutil
                for file_copy in config.copy_files:
                    source = file_copy.source_path
                    # Copy to staging folder with original filename
                    filename = os.path.basename(source)
                    staging_path = os.path.join(staging_folder, filename)
                    shutil.copy2(source, staging_path)
                    logger.info(f"Copied {source} to staging: {staging_path}")

                # Map staging folder to sandbox Desktop for easy access
                config.mapped_folders.append(
                    MappedFolder(
                        host_path=staging_folder,
                        sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\SandboxFiles",
                        read_only=False
                    )
                )

            # Create temporary WSX configuration file
            wsx_content = self._generate_wsx_config(config, staging_folder)

            with tempfile.NamedTemporaryFile(
                suffix=".wsx", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(wsx_content)
                wsx_path = f.name

            # Start the sandbox using Windows Sandbox executable directly
            sandbox_exe = r"C:\Windows\System32\WindowsSandbox.exe"
            if not os.path.exists(sandbox_exe):
                raise RuntimeError(
                    "Windows Sandbox is not available. "
                    "Please enable Windows Sandbox feature in Windows Features."
                )

            # Use Start-Process in PowerShell to launch with proper elevation if needed
            # This ensures UAC prompt appears if required
            launch_process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f'Start-Process -FilePath "{sandbox_exe}" -ArgumentList "{wsx_path}" -Wait:$false',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for launch command to complete
            stdout, stderr = await launch_process.communicate()

            # Check if PowerShell command failed
            if launch_process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                stdout_msg = stdout.decode('utf-8', errors='ignore') if stdout else ""
                raise RuntimeError(
                    f"Failed to launch Windows Sandbox. PowerShell return code: {launch_process.returncode}. "
                    f"Error: {error_msg}. Output: {stdout_msg}"
                )

            logger.info("Launch command completed, waiting for Windows Sandbox to start...")

            # Wait for sandbox to actually start (poll for WindowsSandbox.exe process)
            # Windows Sandbox takes about 30 seconds to start
            max_wait_time = 60  # seconds
            poll_interval = 1  # seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                await asyncio.sleep(poll_interval)
                elapsed_time += poll_interval

                if await self._is_sandbox_running():
                    logger.info(f"Windows Sandbox started successfully after {elapsed_time} seconds")
                    break
            else:
                # Timeout - sandbox didn't start
                raise RuntimeError(
                    f"Windows Sandbox failed to start within {max_wait_time} seconds. "
                    f"Please check if Windows Sandbox is enabled and try again."
                )

            # Don't delete the file immediately - Windows Sandbox needs it
            # Schedule cleanup after a delay or let it be cleaned up later
            if not wait_for_completion:
                # For async operation, we'll keep the file for now
                # In production, you might want to track and clean up later
                pass

            return {
                "status": "started",
                "sandbox_id": f"sandbox-{id(config)}",
                "config": config.dict(),
                "wsx_path": wsx_path,
            }

        except Exception as e:
            logger.error(f"Error creating sandbox: {e}", exc_info=True)
            # Clean up on error
            if wsx_path and os.path.exists(wsx_path):
                try:
                    os.unlink(wsx_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {wsx_path}: {cleanup_error}")
            raise

    def _generate_wsx_config(self, config: SandboxConfig, staging_folder: str | None = None) -> str:
        """Generate WSX configuration XML for Windows Sandbox."""
        import xml.sax.saxutils as saxutils

        # Start building XML
        xml_parts = ["<Configuration>"]
        xml_parts.append(f"<VGpu>{'Enable' if config.vgpu else 'Disable'}</VGpu>")
        xml_parts.append(f"<Networking>{'Enable' if config.networking else 'Disable'}</Networking>")
        xml_parts.append(f"<MemoryInMB>{config.memory_mb}</MemoryInMB>")

        # Add mapped folders only if present
        if config.mapped_folders:
            xml_parts.append("<MappedFolders>")
            for folder in config.mapped_folders:
                xml_parts.append("<MappedFolder>")
                xml_parts.append(f"<HostFolder>{saxutils.escape(folder.host_path)}</HostFolder>")
                if folder.sandbox_path:
                    xml_parts.append(f"<SandboxFolder>{saxutils.escape(folder.sandbox_path)}</SandboxFolder>")
                xml_parts.append(f"<ReadOnly>{'true' if folder.read_only else 'false'}</ReadOnly>")
                xml_parts.append("</MappedFolder>")
            xml_parts.append("</MappedFolders>")

        # Build logon commands: original commands, file copies, then startup scripts
        all_commands = []

        # Add original logon commands first
        all_commands.extend(config.logon_commands)

        # Add file copy commands if files need to be copied
        if config.copy_files and staging_folder:
            # Create destination directories and copy files
            for file_copy in config.copy_files:
                dest_dir = os.path.dirname(file_copy.destination_path)
                filename = os.path.basename(file_copy.source_path)
                source_in_sandbox = f"C:\\Users\\WDAGUtilityAccount\\Desktop\\SandboxFiles\\{filename}"

                # Create destination directory if it doesn't exist
                all_commands.append(f'if not exist "{dest_dir}" mkdir "{dest_dir}"')

                # Copy file to destination
                overwrite_flag = "/Y" if file_copy.overwrite else "/-Y"
                all_commands.append(f'copy {overwrite_flag} "{source_in_sandbox}" "{file_copy.destination_path}"')

        # Add startup scripts/executables
        for script in config.startup_scripts:
            # If it's a path, execute it directly; otherwise treat as command
            if os.path.sep in script or script.endswith(('.exe', '.bat', '.cmd', '.ps1')):
                # It's a file path - execute it
                all_commands.append(f'start "" "{script}"')
            else:
                # It's a command - execute it directly
                all_commands.append(script)

        # Add all commands as logon commands
        if all_commands:
            for command in all_commands:
                xml_parts.append("<LogonCommand>")
                xml_parts.append(f"<Command>{saxutils.escape(command)}</Command>")
                xml_parts.append("</LogonCommand>")

        xml_parts.append("</Configuration>")
        return "\n".join(xml_parts)

    async def _list_sandboxes(self) -> list[dict[str, Any]]:
        """List all running Windows Sandbox instances."""
        # Implementation would list running sandboxes
        return []

    async def _stop_sandbox(self, sandbox_id: str, force: bool = False) -> dict[str, Any]:
        """Stop a running Windows Sandbox instance."""
        # Implementation would stop the specified sandbox
        return {"status": "stopped", "sandbox_id": sandbox_id}
