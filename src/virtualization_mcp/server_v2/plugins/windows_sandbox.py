"""Windows Sandbox plugin for virtualization-mcp.

This plugin provides integration with Windows Sandbox for running applications in an isolated environment.
"""
import asyncio
import json
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import aiofiles
from fastapi import APIRouter, HTTPException, status, UploadFile, File

from virtualization_mcp.server_v2.plugins.base import BasePlugin
from virtualization_mcp.server_v2.plugins import register_plugin
from ..utils.windows_sandbox_helper import WindowsSandboxHelper, WindowsSandboxError

logger = logging.getLogger(__name__)

@register_plugin("windows_sandbox")
class WindowsSandboxPlugin(BasePlugin):
    """Windows Sandbox plugin for managing lightweight, disposable sandboxes."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Windows Sandbox plugin.
        
        Args:
            config: Plugin configuration dictionary
        """
        super().__init__(config)
        
        # Configuration
        self.sandbox_dir = Path(config.get("sandbox_dir", "./sandboxes"))
        self.default_memory_mb = int(config.get("default_memory_mb", 4096))
        self.default_vcpu_count = int(config.get("default_vcpu_count", 2))
        
        # Ensure directories exist
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize Windows Sandbox helper
            self.sandbox_helper = WindowsSandboxHelper(sandbox_dir=self.sandbox_dir)
            logger.info("Windows Sandbox helper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Windows Sandbox helper: {e}")
            raise RuntimeError("Windows Sandbox is not available on this system") from e
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self) -> None:
        """Set up API routes for Windows Sandbox operations."""
        @self.router.post("/sandboxes/create")
        async def create_sandbox(
            name: str,
            memory_mb: int = None,
            vcpu_count: int = None,
            template: str = "default",
            shared_folders: List[Dict[str, str]] = None
        ) -> Dict[str, Any]:
            """Create a new Windows Sandbox instance."""
            if name in self.active_sandboxes:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Sandbox with name '{name}' already exists"
                )
            
            # Start sandbox in background
            task = asyncio.create_task(
                self._create_sandbox(name, memory_mb, vcpu_count, template, shared_folders or [])
            )
            
            # Store task and basic info
            self.active_sandboxes[name] = {
                "task": task,
                "status": "starting",
                "created_at": self._now_iso(),
                "config": {
                    "memory_mb": memory_mb or self.default_memory_mb,
                    "vcpu_count": vcpu_count or self.default_vcpu_count,
                    "template": template,
                    "shared_folders": shared_folders or []
                }
            }
            
            # Clean up when done
            task.add_done_callback(
                lambda t, n=name: self._cleanup_sandbox(n)
            )
            
            return {
                "status": "creating",
                "name": name,
                "message": f"Sandbox '{name}' is being created"
            }
        
        @self.router.get("/sandboxes")
        async def list_sandboxes() -> List[Dict[str, Any]]:
            """List all active sandboxes."""
            result = []
            for name, sandbox in self.active_sandboxes.items():
                result.append({
                    "name": name,
                    "status": sandbox["status"],
                    "created_at": sandbox["created_at"],
                    "config": sandbox["config"]
                })
            return result
        
        @self.router.post("/sandboxes/{name}/execute")
        async def execute_in_sandbox(
            name: str,
            command: str,
            wait: bool = True,
            timeout: int = 60
        ) -> Dict[str, Any]:
            """Execute a command in the sandbox."""
            if name not in self.active_sandboxes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sandbox '{name}' not found"
                )
            
            try:
                # In a real implementation, this would use Windows Sandbox's API
                # to execute the command in the sandbox
                result = await self._execute_in_sandbox(name, command, wait, timeout)
                return {
                    "status": "success",
                    "sandbox": name,
                    "command": command,
                    "result": result
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error executing command: {str(e)}"
                )
        
        @self.router.post("/sandboxes/{name}/upload")
        async def upload_to_sandbox(
            name: str,
            file: UploadFile = File(...),
            destination: str = "C:\\Users\\WDAGUtilityAccount\\Desktop"
        ) -> Dict[str, Any]:
            """Upload a file to the sandbox."""
            if name not in self.active_sandboxes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sandbox '{name}' not found"
                )
            
            try:
                # In a real implementation, this would copy the file to the sandbox
                # using Windows Sandbox's file sharing capabilities
                file_path = await self._upload_to_sandbox(name, file, destination)
                return {
                    "status": "success",
                    "sandbox": name,
                    "file_path": file_path,
                    "original_filename": file.filename,
                    "size": file.size
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error uploading file: {str(e)}"
                )
        
        @self.router.post("/sandboxes/{name}/terminate")
        async def terminate_sandbox(name: str, force: bool = False) -> Dict[str, Any]:
            """Terminate a running sandbox."""
            if name not in self.active_sandboxes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sandbox '{name}' not found"
                )
            
            try:
                await self._terminate_sandbox(name, force)
                return {
                    "status": "terminating",
                    "sandbox": name,
                    "message": f"Sandbox '{name}' is being terminated"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error terminating sandbox: {str(e)}"
                )
    
    async def _create_sandbox(
        self,
        name: str,
        memory_mb: Optional[int],
        vcpu_count: Optional[int],
        template: str,
        shared_folders: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Internal method to create a Windows Sandbox instance."""
        try:
            # Create the sandbox using the helper
            result = await self.sandbox_helper.create_sandbox(
                name=name,
                memory_mb=memory_mb or self.default_memory_mb,
                vcpu_count=vcpu_count or self.default_vcpu_count,
                shared_folders=shared_folders,
                template=template
            )
            
            # Store sandbox information
            self.active_sandboxes[name] = {
                "status": "running",
                "created_at": self._now_iso(),
                "config": {
                    "memory_mb": memory_mb or self.default_memory_mb,
                    "vcpu_count": vcpu_count or self.default_vcpu_count,
                    "template": template,
                    "shared_folders": shared_folders or []
                },
                "sandbox_info": result
            }
            
            return {
                "status": "running",
                "name": name,
                "memory_mb": memory_mb or self.default_memory_mb,
                "vcpu_count": vcpu_count or self.default_vcpu_count,
                "template": template,
                "shared_folders": shared_folders,
                "sandbox_info": result
            }
            
        except WindowsSandboxError as e:
            logger.error(f"Windows Sandbox error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create sandbox: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating sandbox: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating sandbox: {str(e)}"
            )
    
    async def _execute_in_sandbox(
        self,
        name: str,
        command: str,
        wait: bool = True,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        if name not in self.active_sandboxes:
            raise ValueError(f"Sandbox '{name}' not found")
            
        try:
            # Execute the command using the helper
            result = await self.sandbox_helper.execute_command(
                sandbox_name=name,
                command=command,
                wait=wait,
                timeout=timeout
            )
            
            return result
            
        except WindowsSandboxError as e:
            logger.error(f"Error executing command in sandbox: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute command in sandbox: {str(e)}"
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error executing command: {str(e)}"
            )
    
    async def _upload_to_sandbox(
        self,
        name: str,
        file: UploadFile,
        destination: str
    ) -> str:
        """Upload a file to the sandbox."""
        if name not in self.active_sandboxes:
            raise ValueError(f"Sandbox '{name}' not found")
            
        try:
            # Save the uploaded file to a temporary location
            temp_dir = self.sandbox_dir / "temp"
            temp_dir.mkdir(exist_ok=True, parents=True)
            
            temp_file = temp_dir / f"{uuid.uuid4()}_{file.filename}"
            
            # Save the file asynchronously
            async with aiofiles.open(temp_file, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            # Upload the file to the sandbox
            result = await self.sandbox_helper.upload_file(
                sandbox_name=name,
                source_path=temp_file,
                destination_path=destination
            )
            
            # Clean up the temporary file
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
            
            return result["destination_path"]
            
        except WindowsSandboxError as e:
            logger.error(f"Error uploading file to sandbox: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to sandbox: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error uploading file: {str(e)}"
            )
    
    async def _terminate_sandbox(self, name: str, force: bool = False) -> None:
        """Terminate a running sandbox."""
        if name not in self.active_sandboxes:
            raise ValueError(f"Sandbox '{name}' not found")
            
        try:
            # Terminate the sandbox using the helper
            result = await self.sandbox_helper.terminate_sandbox(
                sandbox_name=name,
                force=force
            )
            
            # Update status
            if name in self.active_sandboxes:
                self.active_sandboxes[name]["status"] = "terminated"
            
            logger.info(f"Terminated sandbox '{name}': {result}")
            
        except WindowsSandboxError as e:
            logger.error(f"Error terminating sandbox: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to terminate sandbox: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error terminating sandbox: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error terminating sandbox: {str(e)}"
            )
    
    async def _cleanup_sandbox(self, name: str) -> None:
        """Clean up resources for a sandbox."""
        if name in self.active_sandboxes:
            try:
                # Clean up using the helper
                await self.sandbox_helper._cleanup_sandbox(name)
                
                # Remove from active sandboxes
                self.active_sandboxes.pop(name, None)
                
                logger.info(f"Cleaned up resources for sandbox '{name}'")
                
            except Exception as e:
                logger.error(f"Error cleaning up sandbox '{name}': {e}", exc_info=True)
    
    def _create_wsb_config(
        self,
        name: str,
        memory_mb: int,
        vcpu_count: int,
        shared_folders: List[Dict[str, str]],
        template: str = "default"
    ) -> str:
        """Create a Windows Sandbox configuration file.
        
        Note: This method is kept for backward compatibility but the actual
        WSB configuration is now handled by the WindowsSandboxHelper class.
        
        Args:
            name: Name of the sandbox
            memory_mb: Memory in MB to allocate
            vcpu_count: Number of virtual CPUs to allocate
            shared_folders: List of folders to share with the sandbox
            template: Template name (not currently used)
            
        Returns:
            A placeholder string (actual WSB configuration is handled by the helper)
        """
        # This method is now a compatibility wrapper around the helper
        # The actual WSB configuration is handled by WindowsSandboxHelper._create_wsb_config
        return f"WSB configuration for {name} (handled by WindowsSandboxHelper)"
    
    def _dict_to_xml(self, data: Dict[str, Any]) -> str:
        """Convert a dictionary to an XML string."""
        def _to_xml(element, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(element, key)
                            _to_xml(child, item)
                    else:
                        child = ET.SubElement(element, key)
                        _to_xml(child, value)
            else:
                element.text = str(data)
        
        root = ET.Element("Configuration")
        _to_xml(root, data)
        
        # Format with indentation
        from xml.dom import minidom
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")
    
    def _now_iso(self) -> str:
        """Get current time in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    async def startup(self) -> None:
        """Startup tasks."""
        await super().startup()
        logger.info("Windows Sandbox plugin started")
    
    async def shutdown(self) -> None:
        """Shutdown tasks."""
        # Terminate all active sandboxes
        for name in list(self.active_sandboxes.keys()):
            await self._terminate_sandbox(name, force=True)
        
        await super().shutdown()
        logger.info("Windows Sandbox plugin stopped")
