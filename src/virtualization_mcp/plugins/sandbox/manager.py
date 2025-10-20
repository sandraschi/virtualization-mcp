"""
Windows Sandbox Helper for virtualization-mcp

This module provides Windows Sandbox management functionality.
"""

import asyncio
import logging
import os
import tempfile
from enum import Enum
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SandboxState(str, Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"
    STARTING = "Starting"
    STOPPING = "Stopping"
    ERROR = "Error"


class MappedFolder(BaseModel):
    """Model for Windows Sandbox folder mapping."""

    host_path: str = Field(..., description="Path on host machine (must exist and be absolute)")
    sandbox_path: str = Field(default="", description="Path in sandbox (optional, defaults to Desktop)")
    read_only: bool = Field(default=False, description="Whether folder is read-only in sandbox")

    @field_validator("host_path")
    @classmethod
    def validate_host_path(cls, v: str) -> str:
        """Validate that host path exists and is absolute."""
        from pathlib import Path
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(f"Host path must be absolute: {v}")
        if not path.exists():
            raise ValueError(f"Host path does not exist: {v}")
        return str(path)


class SandboxConfig(BaseModel):
    """Configuration for Windows Sandbox."""

    name: str = Field(..., description="Name of the sandbox configuration")
    memory_mb: int = Field(4096, ge=1024, le=32768, description="Memory in MB (1024-32768)")
    vgpu: bool = Field(True, description="Enable virtual GPU")
    networking: bool = Field(True, description="Enable networking")
    mapped_folders: list[MappedFolder] = Field(
        default_factory=list, description="List of folders to map into the sandbox"
    )
    logon_commands: list[str] = Field(
        default_factory=list, description="Commands to run on sandbox startup"
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

    async def initialize(self, mcp: FastMCP) -> None:
        """Initialize the Windows Sandbox helper."""
        if self.initialized:
            return

        self.mcp = mcp
        self.initialized = True
        logger.info("Windows Sandbox Helper initialized")

    def register_tools(self, mcp: FastMCP) -> None:
        """Register Windows Sandbox tools with FastMCP."""
        if not self.initialized:
            raise RuntimeError("Helper not initialized. Call initialize() first.")

        @mcp.tool("create_windows_sandbox")
        async def create_sandbox(
            config: SandboxConfig, wait_for_completion: bool = False
        ) -> dict[str, Any]:
            """Create and start a new Windows Sandbox instance.

            Args:
                config: Sandbox configuration
                wait_for_completion: Whether to wait for sandbox to fully start
            """
            return await self._create_sandbox(config, wait_for_completion)

        @mcp.tool("list_running_sandboxes")
        async def list_sandboxes() -> list[dict[str, Any]]:
            """List all running Windows Sandbox instances."""
            return await self._list_sandboxes()

        @mcp.tool("stop_sandbox")
        async def stop_sandbox(sandbox_id: str, force: bool = False) -> dict[str, Any]:
            """Stop a running Windows Sandbox instance.

            Args:
                sandbox_id: ID of the sandbox to stop
                force: Whether to force stop the sandbox
            """
            return await self._stop_sandbox(sandbox_id, force)

    # Implementation methods
    async def _create_sandbox(
        self, config: SandboxConfig, wait_for_completion: bool = False
    ) -> dict[str, Any]:
        """Create and start a new Windows Sandbox instance."""
        try:
            # Create temporary WSX configuration file
            wsx_content = self._generate_wsx_config(config)

            with tempfile.NamedTemporaryFile(
                suffix=".wsx", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(wsx_content)
                wsx_path = f.name

            # Start the sandbox
            cmd = f'Start-Process -FilePath "{wsx_path}" -Wait'
            await asyncio.create_subprocess_shell(
                f'powershell -Command "{cmd}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Clean up the temporary file
            try:
                os.unlink(wsx_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {wsx_path}: {e}")

            return {
                "status": "started",
                "sandbox_id": f"sandbox-{id(config)}",
                "config": config.dict(),
            }

        except Exception as e:
            logger.error(f"Error creating sandbox: {e}")
            raise

    def _generate_wsx_config(self, config: SandboxConfig) -> str:
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

        # Add logon commands only if present
        if config.logon_commands:
            for command in config.logon_commands:
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
