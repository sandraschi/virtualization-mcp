"""
MCP Tool Discovery and Documentation

This module provides tools for discovering and documenting MCP tools
in a way that's compatible with stdio-based MCP clients like Claude Desktop.
"""

from typing import Dict, List, Any, Optional, Type, get_type_hints
import inspect
import json
from functools import wraps

import asyncio
from typing import Any, Dict, List, Optional, Type, get_type_hints
import inspect
import json
from functools import wraps

from fastmcp import FastMCP

class MCPToolDiscovery:
    """Handles discovery and documentation of MCP tools."""
    
    def __init__(self, mcp: FastMCP):
        """Initialize with an MCP instance."""
        self.mcp = mcp
        self.tool_cache = {}
        
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get info for
            
        Returns:
            Dictionary containing tool information
        """
        if not hasattr(self.mcp, '_tools') or tool_name not in self.mcp._tools:
            return {"error": f"Tool '{tool_name}' not found"}
            
        tool = self.mcp._tools[tool_name]
        if not hasattr(tool, 'func'):
            return {"error": f"Tool '{tool_name}' has no function implementation"}
            
        return self._describe_tool(tool_name, tool)
    
    def list_tools(self, category: Optional[str] = None, 
                  search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools with optional filtering.
        
        Args:
            category: Filter tools by category
            search: Search term to filter tools
            
        Returns:
            List of tool information dictionaries
        """
        if not hasattr(self.mcp, '_tools'):
            return []
            
        tools = []
        for name, tool in self.mcp._tools.items():
            if name.startswith('_') or not hasattr(tool, 'func'):
                continue
                
            tool_info = self._describe_tool(name, tool)
            
            # Apply filters
            if category and category.lower() not in tool_info.get('categories', []):
                continue
                
            if search and not self._matches_search(tool_info, search):
                continue
                
            tools.append(tool_info)
            
        return tools
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the JSON schema for a tool's parameters.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            JSON schema for the tool's parameters
        """
        if not hasattr(self.mcp, '_tools') or tool_name not in self.mcp._tools:
            return {"error": f"Tool '{tool_name}' not found"}
            
        tool = self.mcp._tools[tool_name]
        if not hasattr(tool, 'func'):
            return {"error": f"Tool '{tool_name}' has no function implementation"}
            
        return self._generate_parameter_schema(tool.func)
    
    def _describe_tool(self, name: str, tool) -> Dict[str, Any]:
        """Generate a description dictionary for a tool."""
        func = tool.func
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ''
        
        # Parse docstring
        doc_lines = [line.strip() for line in docstring.split('\n') if line.strip()]
        summary = doc_lines[0] if doc_lines else ''
        description = '\n'.join(doc_lines[1:]) if len(doc_lines) > 1 else ''
        
        # Extract parameter info
        parameters = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_info = {
                'type': self._get_type_name(param.annotation),
                'required': param.default == param.empty,
                'default': param.default if param.default != param.empty else None
            }
            
            # Try to extract parameter description from docstring
            param_doc = self._extract_param_doc(param_name, docstring)
            if param_doc:
                param_info['description'] = param_doc
                
            parameters[param_name] = param_info
        
        # Build tool info
        tool_info = {
            'name': name,
            'description': summary,
            'long_description': description,
            'parameters': parameters,
            'return_type': self._get_type_name(sig.return_annotation),
            'categories': getattr(tool, 'categories', []),
            'requires_auth': getattr(tool, 'requires_auth', False)
        }
        
        # Add endpoint if available (for HTTP compatibility)
        if hasattr(tool, 'endpoint'):
            tool_info['endpoint'] = tool.endpoint
            tool_info['method'] = getattr(tool, 'method', 'GET').lower()
            
        return tool_info
    
    def _generate_parameter_schema(self, func) -> Dict[str, Any]:
        """Generate a JSON schema for a function's parameters."""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
                
            param_schema = {'type': self._get_json_type(param.annotation)}
            
            if param.default != param.empty:
                param_schema['default'] = param.default
            else:
                required.append(name)
                
            properties[name] = param_schema
            
        return {
            'type': 'object',
            'properties': properties,
            'required': required
        }
    
    @staticmethod
    def _get_type_name(type_obj) -> str:
        """Convert a type object to a string name."""
        if type_obj is inspect.Parameter.empty:
            return 'Any'
        return str(type_obj.__name__) if hasattr(type_obj, '__name__') else str(type_obj)
    
    @staticmethod
    def _get_json_type(python_type) -> str:
        """Map Python types to JSON schema types."""
        type_map = {
            str: 'string',
            int: 'integer',
            float: 'number',
            bool: 'boolean',
            list: 'array',
            dict: 'object'
        }
        
        if python_type in type_map:
            return type_map[python_type]
        return 'string'  # Default to string for unknown types
    
    @staticmethod
    def _extract_param_doc(param_name: str, docstring: str) -> Optional[str]:
        """Extract parameter documentation from docstring."""
        if not docstring:
            return None
            
        # Look for :param param_name: in docstring
        param_prefix = f":param {param_name}:"
        if param_prefix in docstring:
            # Get everything after the param declaration
            param_desc = docstring.split(param_prefix, 1)[1]
            # Take everything up to the next parameter or section
            if ":param" in param_desc:
                param_desc = param_desc.split(":param")[0]
            elif "\n\n" in param_desc:
                param_desc = param_desc.split("\n\n")[0]
            return param_desc.strip()
            
        return None
    
    @staticmethod
    def _matches_search(tool_info: Dict[str, Any], search_term: str) -> bool:
        """Check if a tool matches the search term."""
        search_lower = search_term.lower()
        
        # Search in name, description, and categories
        if (search_lower in tool_info['name'].lower() or
            search_lower in tool_info.get('description', '').lower() or
            search_lower in tool_info.get('long_description', '').lower() or
            any(search_lower in cat.lower() for cat in tool_info.get('categories', []))):
            return True
            
        # Search in parameter names and descriptions
        for param_name, param_info in tool_info.get('parameters', {}).items():
            if (search_lower in param_name.lower() or
                search_lower in param_info.get('description', '').lower()):
                return True
                
        return False

from .services.service_manager import service_manager

def register_mcp_tools(mcp: FastMCP) -> None:
    """Register MCP tool discovery endpoints.
    
    Args:
        mcp: The FastMCP instance to register tools with
    """
    discovery = MCPToolDiscovery(mcp)
    # Get VM service using get_service() method
    vm_service = service_manager.get_service('vm_service')
    
    @mcp.tool(
        name="ListTools",
        description="List all available MCP tools with optional filtering"
    )
    async def list_tools(
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all available MCP tools with optional filtering.
        
        Args:
            category: Filter tools by category (e.g., 'vm', 'network')
            search: Search term to filter tools by name or description
            
        Returns:
            List of tool information dictionaries
            
        Example:
            ```python
            # List all VM-related tools
            tools = await mcp.call("list_tools", {"category": "vm"})
            
            # Search for networking tools
            tools = await mcp.call("list_tools", {"search": "network"})
            ```
        """
        return discovery.list_tools(category=category, search=search)
    
    @mcp.tool(
        name="GetToolInfo",
        description="Get detailed information about a specific tool"
    )
    async def get_tool_info(tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get information about
            
        Returns:
            Dictionary containing detailed tool information
            
        Example:
            ```python
            # Get info about the create_vm tool
            tool_info = await mcp.call("get_tool_info", {"tool_name": "create_vm"})
            print(tool_info['description'])
            ```
        """
        return discovery.get_tool_info(tool_name)
    
    @mcp.tool(
        name="GetToolSchema",
        description="Get the JSON schema for a tool's parameters"
    )
    async def get_tool_schema(tool_name: str) -> Dict[str, Any]:
        """Get the JSON schema for a tool's parameters.
        
        This is useful for generating UIs that need to validate input
        before calling a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            JSON schema for the tool's parameters
            
        Example:
            ```python
            # Get schema for create_vm parameters
            schema = await mcp.call("get_tool_schema", {"tool_name": "create_vm"})
            print(json.dumps(schema, indent=2))
            ```
        """
        return discovery.get_tool_schema(tool_name)

    # --- VM Service Tools ---
    vm_service = service_manager.vm_service

    @mcp.tool(
        name="ListVms",
        description="List all VirtualBox virtual machines with their current states."
    )
    async def list_vms(details: bool = False, state_filter: str = "all") -> Dict[str, Any]:
        """List all VirtualBox virtual machines with their current states.

        Args:
            details: If True, returns detailed information for each VM.
            state_filter: Filter VMs by state (e.g., 'running', 'poweroff').

        Returns:
            A dictionary containing the list of VMs and their status.
        """
        return await asyncio.to_thread(vm_service.list_vms, details=details, state_filter=state_filter)

    @mcp.tool(
        name="GetVmState",
        description="Get the current state of a virtual machine."
    )
    async def get_vm_state(vm_name: str) -> Dict[str, Any]:
        """Get the current state of a virtual machine.

        Args:
            vm_name: Name of the virtual machine.

        Returns:
            A dictionary containing the VM's state.
        """
        return await asyncio.to_thread(vm_service.get_vm_state, vm_name=vm_name)

    @mcp.tool(
        name="CreateVm",
        description="Create a new VirtualBox virtual machine."
    )
    async def create_vm(name: str, template: str = "ubuntu-dev", memory_mb: Optional[int] = None, disk_gb: Optional[int] = None) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.create_vm, name=name, template=template, memory_mb=memory_mb, disk_gb=disk_gb)

    @mcp.tool(
        name="StartVm",
        description="Start a VirtualBox virtual machine."
    )
    async def start_vm(name: str, headless: bool = True) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.start_vm, name=name, headless=headless)

    @mcp.tool(
        name="StopVm",
        description="Stop a running VirtualBox virtual machine."
    )
    async def stop_vm(name: str, force: bool = False) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.stop_vm, name=name, force=force)

    @mcp.tool(
        name="DeleteVm",
        description="Delete a VirtualBox virtual machine."
    )
    async def delete_vm(name: str, delete_disk: bool = True) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.delete_vm, name=name, delete_disk=delete_disk)

    @mcp.tool(
        name="CreateSnapshot",
        description="Create a snapshot of a virtual machine."
    )
    async def create_snapshot(vm_name: str, snapshot_name: str, description: str = "") -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.create_snapshot, vm_name=vm_name, snapshot_name=snapshot_name, description=description)

    @mcp.tool(
        name="ListSnapshots",
        description="List all snapshots for a virtual machine."
    )
    async def list_snapshots(vm_name: str) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.list_snapshots, vm_name=vm_name)

    @mcp.tool(
        name="RestoreSnapshot",
        description="Restore a virtual machine to a previous snapshot."
    )
    async def restore_snapshot(vm_name: str, snapshot_name: str, start_vm: bool = False) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.restore_snapshot, vm_name=vm_name, snapshot_name=snapshot_name, start_vm=start_vm)

    @mcp.tool(
        name="DeleteSnapshot",
        description="Delete a snapshot from a virtual machine."
    )
    async def delete_snapshot(vm_name: str, snapshot_name: str) -> Dict[str, Any]:
        return await asyncio.to_thread(vm_service.delete_snapshot, vm_name=vm_name, snapshot_name=snapshot_name)

    # --- ISO and Media Management ---
    @mcp.tool(
        name="ListIsos",
        description="List all available ISO files in the VirtualBox media library."
    )
    async def list_isos() -> Dict[str, Any]:
        """List all available ISO files that can be mounted on VMs."""
        return await asyncio.to_thread(vm_service.list_media, media_type='iso')

    @mcp.tool(
        name="MountIso",
        description="Mount an ISO file to a virtual machine's optical drive."
    )
    async def mount_iso(vm_name: str, iso_path: str, controller_name: str = 'IDE Controller', port: int = 1, device: int = 0) -> Dict[str, Any]:
        """Mount an ISO file to a VM's optical drive.
        
        Args:
            vm_name: Name of the virtual machine
            iso_path: Path to the ISO file
            controller_name: Name of the storage controller (default: 'IDE Controller')
            port: Controller port number (default: 1)
            device: Device number on the port (default: 0)
        """
        return await asyncio.to_thread(
            vm_service.mount_iso, 
            vm_name=vm_name, 
            iso_path=iso_path,
            controller_name=controller_name,
            port=port,
            device=device
        )

    @mcp.tool(
        name="UnmountIso",
        description="Unmount an ISO from a virtual machine's optical drive."
    )
    async def unmount_iso(vm_name: str, controller_name: str = 'IDE Controller', port: int = 1, device: int = 0) -> Dict[str, Any]:
        """Unmount an ISO from a VM's optical drive."""
        return await asyncio.to_thread(
            vm_service.unmount_iso,
            vm_name=vm_name,
            controller_name=controller_name,
            port=port,
            device=device
        )

    # --- Network Configuration ---
    @mcp.tool(
        name="ListNetworkAdapters",
        description="List network adapters for a virtual machine."
    )
    async def list_network_adapters(vm_name: str) -> Dict[str, Any]:
        """List all network adapters for a VM."""
        return await asyncio.to_thread(vm_service.list_network_adapters, vm_name=vm_name)

    @mcp.tool(
        name="ConfigureNetworkAdapter",
        description="Configure a network adapter for a virtual machine."
    )
    async def configure_network_adapter(
        vm_name: str,
        adapter_id: int,
        enabled: bool = True,
        network_type: str = 'nat',
        mac_address: Optional[str] = None,
        cable_connected: bool = True
    ) -> Dict[str, Any]:
        """Configure a network adapter for a VM."""
        return await asyncio.to_thread(
            vm_service.configure_network_adapter,
            vm_name=vm_name,
            adapter_id=adapter_id,
            enabled=enabled,
            network_type=network_type,
            mac_address=mac_address,
            cable_connected=cable_connected
        )

    # --- Storage Management ---
    @mcp.tool(
        name="ListStorageControllers",
        description="List storage controllers for a virtual machine."
    )
    async def list_storage_controllers(vm_name: str) -> Dict[str, Any]:
        """List all storage controllers for a VM."""
        return await asyncio.to_thread(vm_service.list_storage_controllers, vm_name=vm_name)

    @mcp.tool(
        name="CreateDisk",
        description="Create a new virtual disk."
    )
    async def create_disk(
        disk_path: str,
        size_gb: int,
        format_type: str = 'vdi',
        variant: str = 'Standard',
        resizeable: bool = True
    ) -> Dict[str, Any]:
        """Create a new virtual disk."""
        return await asyncio.to_thread(
            vm_service.create_disk,
            disk_path=disk_path,
            size_gb=size_gb,
            format_type=format_type,
            variant=variant,
            resizeable=resizeable
        )

    @mcp.tool(
        name="AttachDisk",
        description="Attach a disk to a virtual machine."
    )
    async def attach_disk(
        vm_name: str,
        disk_path: str,
        controller_name: str = 'SATA Controller',
        port: int = 0,
        device: int = 0,
        type: str = 'hdd'
    ) -> Dict[str, Any]:
        """Attach a disk to a VM."""
        return await asyncio.to_thread(
            vm_service.attach_disk,
            vm_name=vm_name,
            disk_path=disk_path,
            controller_name=controller_name,
            port=port,
            device=device,
            type=type
        )

    # --- VM Configuration ---
    @mcp.tool(
        name="ModifyVm",
        description="Modify virtual machine settings."
    )
    async def modify_vm(
        vm_name: str,
        memory_mb: Optional[int] = None,
        cpu_count: Optional[int] = None,
        vram_mb: Optional[int] = None,
        nested_virt: Optional[bool] = None,
        io_apic: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Modify VM settings."""
        return await asyncio.to_thread(
            vm_service.modify_vm,
            vm_name=vm_name,
            memory_mb=memory_mb,
            cpu_count=cpu_count,
            vram_mb=vram_mb,
            nested_virt=nested_virt,
            io_apic=io_apic
        )

    # --- System Information ---
    @mcp.tool(
        name="GetSystemInfo",
        description="Get information about the host system and VirtualBox installation."
    )
    async def get_system_info() -> Dict[str, Any]:
        """Get system and VirtualBox information."""
        return await asyncio.to_thread(vm_service.get_system_info)

    @mcp.tool(
        name="GetVmMetrics",
        description="Get performance metrics for a running virtual machine."
    )
    async def get_vm_metrics(vm_name: str) -> Dict[str, Any]:
        """Get VM performance metrics."""
        return await asyncio.to_thread(vm_service.get_vm_metrics, vm_name=vm_name)

    @mcp.tool(
        name="GetVmScreenshot",
        description="Take a screenshot of a running virtual machine."
    )
    async def get_vm_screenshot(
        vm_name: str,
        output_file: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """Take a screenshot of a running VM."""
        return await asyncio.to_thread(
            vm_service.take_screenshot,
            vm_name=vm_name,
            output_file=output_file,
            width=width,
            height=height
        )
