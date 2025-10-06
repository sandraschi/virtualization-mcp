"""
API documentation generator for the VirtualBox MCP server.

This module provides tools to generate OpenAPI/Swagger documentation
for all registered API endpoints.
"""

import inspect
from typing import Dict, List, Any, Optional, Callable, Type, get_type_hints
from functools import wraps
import json
from datetime import datetime

from fastmcp import FastMCP

# Base OpenAPI specification
BASE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "VirtualBox MCP API",
        "description": "RESTful API for managing VirtualBox virtual machines",
        "version": "1.0.0",
        "contact": {
            "name": "VirtualBox MCP Support",
            "url": "https://github.com/yourusername/virtualization-mcp"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development server"
        }
    ],
    "tags": [
        {"name": "VM Lifecycle", "description": "VM creation, startup, and management"},
        {"name": "VM Configuration", "description": "VM configuration and settings"},
        {"name": "Snapshots", "description": "VM snapshot management"},
        {"name": "Storage", "description": "VM storage management"},
        {"name": "Networking", "description": "VM network configuration"},
        {"name": "Devices", "description": "VM device management"},
        {"name": "Templates", "description": "VM templates"},
        {"name": "Metrics", "description": "VM metrics and monitoring"},
        {"name": "Audio/Video", "description": "Audio and video settings"},
        {"name": "System", "description": "System-level operations"}
    ],
    "paths": {},
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["error"]},
                    "message": {"type": "string"},
                    "code": {"type": "integer", "format": "int32"},
                    "details": {"type": "object"}
                },
                "required": ["status", "message", "code"]
            },
            "VM": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "state": {"type": "string"},
                    "os_type": {"type": "string"},
                    "memory_mb": {"type": "integer"},
                    "cpu_count": {"type": "integer"},
                    "storage_gb": {"type": "number"},
                    "network_adapters": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/NetworkAdapter"}
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "state"]
            },
            "NetworkAdapter": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "mac_address": {"type": "string"},
                    "connected": {"type": "boolean"},
                    "ip_addresses": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "type", "connected"]
            },
            "Snapshot": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "is_current": {"type": "boolean"}
                },
                "required": ["id", "name", "created_at"]
            }
        },
        "securitySchemes": {
            "apiKey": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header"
            }
        }
    }
}

class APIDocumentation:
    """Generates and serves API documentation."""
    
    def __init__(self, mcp: FastMCP):
        """Initialize the API documentation generator.
        
        Args:
            mcp: The FastMCP instance to document.
        """
        self.mcp = mcp
        self.spec = dict(BASE_OPENAPI_SPEC)
        self.spec["info"]["generated_at"] = datetime.utcnow().isoformat() + "Z"
    
    def generate_openapi_spec(self) -> dict:
        """Generate the OpenAPI specification for all registered endpoints.
        
        Returns:
            dict: The complete OpenAPI specification.
        """
        # Get all registered tools
        tools = self.mcp._tools if hasattr(self.mcp, "_tools") else {}
        
        # Group tools by path
        endpoints = {}
        for name, tool in tools.items():
            # Skip internal tools
            if name.startswith('_') or not hasattr(tool, 'endpoint'):
                continue
                
            # Get endpoint metadata
            endpoint = tool.endpoint
            method = tool.method.lower()
            
            # Initialize path if it doesn't exist
            if endpoint not in self.spec["paths"]:
                self.spec["paths"][endpoint] = {}
            
            # Add endpoint documentation
            self.spec["paths"][endpoint][method] = self._generate_endpoint_doc(tool)
        
        return self.spec
    
    def _generate_endpoint_doc(self, tool) -> dict:
        """Generate OpenAPI documentation for a single endpoint.
        
        Args:
            tool: The tool to document.
            
        Returns:
            dict: The OpenAPI operation object.
        """
        # Get function metadata
        func = tool.func
        docstring = inspect.getdoc(func) or ""
        
        # Parse docstring for summary and description
        lines = [line.strip() for line in docstring.split('\n') if line.strip()]
        summary = lines[0] if lines else ""
        description = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        # Get parameters from function signature
        sig = inspect.signature(func)
        parameters = []
        request_body = None
        
        # Add path parameters
        if hasattr(tool, 'url_params'):
            for param_name, param_type in tool.url_params.items():
                param_info = {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": self._get_schema_for_type(param_type)
                }
                parameters.append(param_info)
        
        # Add query parameters
        if hasattr(tool, 'query_params'):
            for param_name, param_type in tool.query_params.items():
                param_info = {
                    "name": param_name,
                    "in": "query",
                    "required": param_name in getattr(tool, 'required_params', []),
                    "schema": self._get_schema_for_type(param_type)
                }
                parameters.append(param_info)
        
        # Add request body if needed
        if hasattr(tool, 'body_schema'):
            request_body = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": tool.body_schema
                    }
                }
            }
        
        # Determine response schemas
        responses = {
            "200": {
                "description": "Successful operation",
                "content": {
                    "application/json": {
                        "schema": self._get_success_response_schema(tool)
                    }
                }
            },
            "400": {
                "description": "Invalid input",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                }
            },
            "500": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                }
            }
        }
        
        # Add rate limiting response
        responses["429"] = {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"}
                }
            },
            "headers": {
                "Retry-After": {
                    "schema": {"type": "integer"},
                    "description": "Number of seconds to wait before retrying"
                }
            }
        }
        
        # Build the operation object
        operation = {
            "tags": [self._get_tag_for_endpoint(tool.endpoint)],
            "summary": summary,
            "description": description,
            "operationId": tool.name,
            "responses": responses
        }
        
        if parameters:
            operation["parameters"] = parameters
            
        if request_body:
            operation["requestBody"] = request_body
        
        # Add security requirements if needed
        if getattr(tool, 'requires_auth', False):
            operation["security"] = [{"apiKey": []}]
        
        return operation
    
    def _get_schema_for_type(self, type_hint) -> dict:
        """Convert a Python type hint to an OpenAPI schema."""
        if type_hint in (str, 'str'):
            return {"type": "string"}
        elif type_hint in (int, 'int'):
            return {"type": "integer"}
        elif type_hint in (float, 'float'):
            return {"type": "number", "format": "float"}
        elif type_hint in (bool, 'bool'):
            return {"type": "boolean"}
        elif hasattr(type_hint, '__origin__') and type_hint.__origin__ is list:
            return {
                "type": "array",
                "items": self._get_schema_for_type(type_hint.__args__[0])
            }
        elif hasattr(type_hint, '__origin__') and type_hint.__origin__ is dict:
            return {
                "type": "object",
                "additionalProperties": self._get_schema_for_type(type_hint.__args__[1])
            }
        else:
            return {"type": "string"}
    
    def _get_success_response_schema(self, tool) -> dict:
        """Get the success response schema for a tool."""
        # Try to get return type from type hints
        return_type = get_type_hints(tool.func).get('return', {})
        
        if return_type == 'VM':
            return {"$ref": "#/components/schemas/VM"}
        elif return_type == 'List[VM]':
            return {
                "type": "array",
                "items": {"$ref": "#/components/schemas/VM"}
            }
        elif return_type == 'Snapshot':
            return {"$ref": "#/components/schemas/Snapshot"}
        elif return_type == 'List[Snapshot]':
            return {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Snapshot"}
            }
        else:
            return {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success"]},
                    "data": {"type": "object"}
                },
                "required": ["status"]
            }
    
    def _get_tag_for_endpoint(self, endpoint: str) -> str:
        """Determine the tag for an endpoint based on its path."""
        if '/vm/' in endpoint:
            return "VM Lifecycle"
        elif '/snapshot/' in endpoint:
            return "Snapshots"
        elif '/storage/' in endpoint:
            return "Storage"
        elif '/network/' in endpoint:
            return "Networking"
        elif '/device/' in endpoint:
            return "Devices"
        elif '/template/' in endpoint:
            return "Templates"
        elif '/metrics/' in endpoint:
            return "Metrics"
        elif any(x in endpoint for x in ['/audio/', '/video/']):
            return "Audio/Video"
        else:
            return "System"

def register_documentation_routes(mcp: FastMCP) -> None:
    """Register API documentation endpoints.
    
    Args:
        mcp: The FastMCP instance to register routes with.
    """
    # Define common tool categories
    TOOL_CATEGORIES = {
        "vm": "Virtual Machine management (create, start, stop, delete VMs)",
        "network": "Network configuration and management",
        "storage": "Storage management (disks, ISOs, storage controllers)",
        "snapshot": "VM snapshot management",
        "system": "System-level operations and host information",
        "metrics": "Performance metrics and monitoring",
        "audio": "Audio device configuration",
        "video": "Video and display settings",
        "usb": "USB device management",
        "shared": "Shared folders and clipboard",
        "guest": "Guest additions and tools",
        "import_export": "VM import/export functionality",
        "templates": "VM templates and cloning",
        "security": "Security and access control",
        "debug": "Debugging and diagnostic tools"
    }
    
    @mcp.tool(
        name="get_tool_categories",
        description="Get a list of all available tool categories",
        endpoint="/tool-categories"
    )
    async def get_tool_categories() -> dict:
        """Return a list of all available tool categories with descriptions.
        
        This endpoint provides a categorized view of all available tools,
        making it easier to discover functionality by area of interest.
        
        Returns:
            dict: A dictionary of category names to their descriptions.
            
        Example:
            ```
            GET /tool-categories
            {
                "status": "success",
                "data": {
                    "vm": "Virtual Machine management (create, start, stop, delete VMs)",
                    "network": "Network configuration and management",
                    "storage": "Storage management (disks, ISOs, storage controllers)",
                    "snapshot": "VM snapshot management",
                    "system": "System-level operations and host information"
                }
            }
            ```
        """
        return {
            "status": "success",
            "data": TOOL_CATEGORIES
        }
    @mcp.tool(
        name="get_tool_info",
        description="Get detailed information about a specific tool by name",
        endpoint="/tools/{tool_name}"
    )
    async def get_tool_info(tool_name: str) -> dict:
        """Return detailed information about a specific tool.
        
        Args:
            tool_name: The name of the tool to get information about.
            
        Returns:
            dict: Detailed information about the requested tool.
            
        Example:
            ```
            GET /tools/get_vm_info
            {
                "status": "success",
                "data": {
                    "name": "get_vm_info",
                    "endpoint": "/api/v1/vms/{vm_id}",
                    "method": "get",
                    "description": "Get detailed information about a VM",
                    "parameters": [
                        {
                            "name": "vm_id",
                            "type": "str",
                            "required": true,
                            "description": "The ID of the VM to get information about"
                        }
                    ],
                    "return_type": "dict",
                    "example": "..."
                }
            }
            ```
        """
        tools = mcp._tools if hasattr(mcp, "_tools") else {}
        
        if tool_name not in tools:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not found",
                "code": 404
            }
            
        tool = tools[tool_name]
        if not hasattr(tool, 'func'):
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' has no function implementation",
                "code": 500
            }
            
        # Get basic tool information
        func = tool.func
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ''
        
        # Parse docstring for summary, description, and examples
        doc_lines = [line.strip() for line in docstring.split('\n') if line.strip()]
        summary = doc_lines[0] if doc_lines else ''
        description = '\n'.join(doc_lines[1:]) if len(doc_lines) > 1 else ''
        
        # Extract parameter information
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_doc = ""
            # Try to extract parameter description from docstring
            if f"{param_name}:" in docstring:
                param_desc = docstring.split(f"{param_name}:")
                if len(param_desc) > 1:
                    param_doc = param_desc[1].split('\n')[0].strip()
            
            param_info = {
                "name": param_name,
                "type": str(param.annotation) if param.annotation != param.empty else "Any",
                "default": param.default if param.default != param.empty else None,
                "required": param.default == param.empty,
                "description": param_doc
            }
            parameters.append(param_info)
        
        # Get return type information
        return_type = str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
        
        # Extract example if available
        example = None
        if 'Example:' in docstring:
            example_section = docstring.split('Example:')
            if len(example_section) > 1 and '```' in example_section[1]:
                example = example_section[1].split('```')[1].strip()
        
        # Build response
        tool_info = {
            "name": tool_name,
            "endpoint": getattr(tool, 'endpoint', ''),
            "method": getattr(tool, 'method', 'GET').lower(),
            "description": summary,
            "long_description": description,
            "parameters": parameters,
            "return_type": return_type,
            "requires_auth": getattr(tool, 'requires_auth', False),
            "rate_limited": getattr(tool, 'rate_limited', True),
            "source_file": inspect.getsourcefile(func) or "",
            "source_line": inspect.getsourcelines(func)[1] if func else 0
        }
        
        if example:
            tool_info["example"] = example
        
        return {
            "status": "success",
            "data": tool_info
        }
    
    @mcp.tool(
        name="get_api_docs",
        description="Get OpenAPI documentation for all available API endpoints",
        endpoint="/api-docs"
    )
    async def get_api_docs() -> dict:
        """Return OpenAPI documentation for all available API endpoints."""
        docs = APIDocumentation(mcp)
        return docs.generate_openapi_spec()
    
    @mcp.tool(
        name="get_api_endpoints",
        description="Get detailed information about all available API endpoints and tools",
        endpoint="/api-endpoints"
    )
    async def get_api_endpoints(
        details: bool = False,
        category: str = None,
        search: str = None
    ) -> dict:
        """Return detailed information about all available API endpoints and tools.
        
        This endpoint provides comprehensive information about all available tools,
        including their parameters, return types, and usage examples. The response
        can be filtered by category or searched for specific terms.
        
        Args:
            details: If True, include full parameter and return type information.
                    If False, return only basic endpoint information.
            category: Filter tools by category (e.g., 'vm', 'network', 'storage').
            search: Search term to filter tools by name or description.
                    
        Returns:
            dict: A dictionary containing information about all available endpoints.
            
        Example:
            ```
            # Get all VM-related tools with detailed information
            GET /api-endpoints?details=true&category=vm
            
            # Search for tools related to networking
            GET /api-endpoints?search=network
            ```
        """
        tools = mcp._tools if hasattr(mcp, "_tools") else {}
        endpoints = {}
        
        # Helper function to determine if a tool matches the search criteria
        def matches_criteria(tool_name: str, tool, endpoint: str, tool_summary: str, tool_description: str) -> bool:
            # Filter by category if specified
            if category:
                category_lower = category.lower()
                endpoint_lower = endpoint.lower()
                if not (category_lower in endpoint_lower or 
                       category_lower in tool_name.lower() or
                       (tool_description and category_lower in tool_description.lower())):
                    return False
            
            # Filter by search term if specified
            if search:
                search_lower = search.lower()
                if not (search_lower in tool_name.lower() or
                      (tool_summary and search_lower in tool_summary.lower()) or
                      (tool_description and search_lower in tool_description.lower()) or
                      (hasattr(tool, 'tags') and any(search_lower in tag.lower() for tag in tool.tags))):
                    return False
                    
            return True
        
        for name, tool in tools.items():
            # Skip internal tools
            if name.startswith('_') or not hasattr(tool, 'endpoint'):
                continue
                
            # Get basic tool information
            endpoint = tool.endpoint
            method = getattr(tool, 'method', 'GET').lower()
            description = getattr(tool, 'description', '')
            func = getattr(tool, 'func', None)
            
            # Get function signature and docstring
            sig = inspect.signature(func) if func else None
            docstring = inspect.getdoc(func) or ''
            
            # Parse docstring for summary and description
            doc_lines = [line.strip() for line in docstring.split('\n') if line.strip()]
            summary = doc_lines[0] if doc_lines else ''
            long_description = '\n'.join(doc_lines[1:]) if len(doc_lines) > 1 else ''
            
            # Check if tool matches the filter criteria
            if not matches_criteria(name, tool, endpoint, summary, long_description):
                continue
            
            # Initialize endpoint if it doesn't exist
            if endpoint not in endpoints:
                endpoints[endpoint] = {}
            
            # Build basic endpoint info
            endpoint_info = {
                "name": name,
                "method": method,
                "summary": summary,
                "description": description or summary,
                "long_description": long_description,
                "requires_auth": getattr(tool, 'requires_auth', False),
                "rate_limited": getattr(tool, 'rate_limited', True),
                "tags": getattr(tool, 'tags', [])
            }
            
            # Add detailed information if requested
            if details and func and sig:
                # Get parameter information
                parameters = []
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                        
                    param_info = {
                        "name": param_name,
                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                        "default": param.default if param.default != param.empty else None,
                        "required": param.default == param.empty and param.default != param.empty
                    }
                    parameters.append(param_info)
                
                # Get return type information
                return_type = "Any"
                if sig.return_annotation != sig.empty:
                    return_type = str(sig.return_annotation)
                
                # Add detailed info
                endpoint_info.update({
                    "parameters": parameters,
                    "return_type": return_type,
                    "signature": str(sig),
                    "source_file": inspect.getsourcefile(func) or "",
                    "source_line": inspect.getsourcelines(func)[1] if func else 0
                })
                
                # Add examples if available in docstring
                if 'Example:' in docstring:
                    example_section = docstring.split('Example:')[1].split('```')[1]
                    endpoint_info["example"] = example_section.strip()
            
            # Add to endpoints
            if method not in endpoints[endpoint]:
                endpoints[endpoint][method] = {}
                
            endpoints[endpoint][method] = endpoint_info
        
        # Add server information
        server_info = {
            "server": {
                "name": "VirtualBox MCP Server",
                "version": "1.0.0",  # Should be imported from package metadata
                "documentation": "/api-docs",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "endpoints": endpoints
        }
        
        return {
            "status": "success",
            "data": server_info
        }



