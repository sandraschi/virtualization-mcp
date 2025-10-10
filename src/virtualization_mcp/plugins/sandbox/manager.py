"""
Windows Sandbox Helper for virtualization-mcp

This module provides Windows Sandbox management functionality.
"""
import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, HttpUrl

logger = logging.getLogger(__name__)

class SandboxState(str, Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"
    STARTING = "Starting"
    STOPPING = "Stopping"
    ERROR = "Error"

class SandboxConfig(BaseModel):
    """Configuration for Windows Sandbox."""
    name: str = Field(..., description="Name of the sandbox configuration")
    memory_mb: int = Field(4096, ge=1024, le=32768, description="Memory in MB (1024-32768)")
    vgpu: bool = Field(True, description="Enable virtual GPU")
    networking: bool = Field(True, description="Enable networking")
    mapped_folders: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of folders to map into the sandbox"
    )
    logon_commands: List[str] = Field(
        default_factory=list,
        description="Commands to run on sandbox startup"
    )
    
    @field_validator('name')
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
            config: SandboxConfig,
            wait_for_completion: bool = False
        ) -> Dict[str, Any]:
            """Create and start a new Windows Sandbox instance.
            
            Args:
                config: Sandbox configuration
                wait_for_completion: Whether to wait for sandbox to fully start
            """
            return await self._create_sandbox(config, wait_for_completion)
            
        @mcp.tool("list_running_sandboxes")
        async def list_sandboxes() -> List[Dict[str, Any]]:
            """List all running Windows Sandbox instances."""
            return await self._list_sandboxes()
            
        @mcp.tool("stop_sandbox")
        async def stop_sandbox(sandbox_id: str, force: bool = False) -> Dict[str, Any]:
            """Stop a running Windows Sandbox instance.
            
            Args:
                sandbox_id: ID of the sandbox to stop
                force: Whether to force stop the sandbox
            """
            return await self._stop_sandbox(sandbox_id, force)
    
    # Implementation methods
    async def _create_sandbox(
        self, 
        config: SandboxConfig,
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """Create and start a new Windows Sandbox instance."""
        try:
            # Create temporary WSX configuration file
            wsx_content = self._generate_wsx_config(config)
            
            with tempfile.NamedTemporaryFile(
                suffix='.wsx', 
                mode='w', 
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(wsx_content)
                wsx_path = f.name
                
            # Start the sandbox
            cmd = f"Start-Process -FilePath \"{wsx_path}\" -Wait"
            proc = await asyncio.create_subprocess_shell(
                f"powershell -Command \"{cmd}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Clean up the temporary file
            try:
                os.unlink(wsx_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {wsx_path}: {e}")
                
            return {
                "status": "started",
                "sandbox_id": f"sandbox-{id(config)}",
                "config": config.dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating sandbox: {e}")
            raise
    
    def _generate_wsx_config(self, config: SandboxConfig) -> str:
        """Generate WSX configuration XML for Windows Sandbox."""
        # This is a simplified example - a real implementation would generate
        # proper XML based on the configuration
        
        # Generate mapped folders XML
        mapped_folders_xml = "".join(
            f'<MappedFolder><HostFolder>{f["host_path"]}</HostFolder>'
            f'<ReadOnly>{"true" if f.get("readonly", False) else "false"}</ReadOnly>'
            '</MappedFolder>' for f in config.mapped_folders
        )
        
        # Generate logon commands XML
        logon_commands_xml = "</Command><Command>".join(config.logon_commands)
        
        return f"""
        <Configuration>
            <VGpu>{'Enable' if config.vgpu else 'Disable'}</VGpu>
            <Networking>{'Enable' if config.networking else 'Disable'}</Networking>
            <MemoryInMB>{config.memory_mb}</MemoryInMB>
            <MappedFolders>
                {mapped_folders_xml}
            </MappedFolders>
            <LogonCommand>
                <Command>{logon_commands_xml}</Command>
            </LogonCommand>
        </Configuration>
        """.strip()
    
    async def _list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all running Windows Sandbox instances."""
        # Implementation would list running sandboxes
        return []
    
    async def _stop_sandbox(self, sandbox_id: str, force: bool = False) -> Dict[str, Any]:
        """Stop a running Windows Sandbox instance."""
        # Implementation would stop the specified sandbox
        return {"status": "stopped", "sandbox_id": sandbox_id}



