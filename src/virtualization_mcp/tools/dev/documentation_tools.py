"""
Documentation Tools for virtualization-mcp

This module provides tools for generating and managing API documentation
following the FastMCP 2.11 standard.
"""
import inspect
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, get_type_hints

from fastapi import HTTPException, status
from pydantic import BaseModel, create_model

# FastMCP 2.11 Documentation Standard Constants
MCP_DOC_VERSION = "2.11.3"
SCHEMA_VERSION = "1.0.0"

class ParameterDocumentation(BaseModel):
    """Documentation for a single API parameter."""
    name: str
    type: str
    required: bool = True
    default: Any = None
    description: str = ""
    example: Any = None
    enum: Optional[List[str]] = None

class EndpointDocumentation(BaseModel):
    """Documentation for a single API endpoint."""
    path: str
    methods: List[str]
    summary: str = ""
    description: str = ""
    parameters: List[ParameterDocumentation] = []
    request_model: Optional[Dict[str, Any]] = None
    response_model: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = []
    tags: List[str] = []
    deprecated: bool = False

class ToolDocumentation(BaseModel):
    """Documentation for an MCP tool."""
    name: str
    description: str
    parameters: List[ParameterDocumentation] = []
    returns: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = []
    deprecated: bool = False

class APIDocumentation(BaseModel):
    """Complete API documentation following FastMCP 2.11 standard."""
    mcp_version: str = MCP_DOC_VERSION
    schema_version: str = SCHEMA_VERSION
    title: str = "virtualization-mcp API"
    version: str = "1.0.0"
    description: str = "virtualization-mcp API Documentation"
    base_path: str = "/"
    tools: Dict[str, ToolDocumentation] = {}
    generated_at: str = datetime.now(timezone.utc).isoformat()

class DocumentationManager:
    """Manager for API documentation generation and management."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.documentation = APIDocumentation(
            title="virtualization-mcp API",
            version="1.0.0",
            description="virtualization-mcp API Documentation"
        )
        self._initialized = True
    
    def generate_tool_documentation(self, tool_func: callable) -> ToolDocumentation:
        """Generate documentation for a tool function.
        
        Args:
            tool_func: The tool function to document
            
        Returns:
            ToolDocumentation: The generated documentation
        """
        # Get function signature and docstring
        sig = inspect.signature(tool_func)
        doc = inspect.getdoc(tool_func) or ""
        
        # Parse docstring for description and parameters
        doc_lines = doc.split('\n')
        description = doc_lines[0] if doc_lines else ""
        
        # Parse parameters from docstring
        params_doc = {}
        current_param = None
        
        for line in doc_lines[1:]:
            line = line.strip()
            if line.startswith(':param '):
                param_name = line[7:].split(':')[0].strip()
                param_desc = line[line.find(':')+1:].strip()
                params_doc[param_name] = param_desc
                current_param = param_name
            elif line.startswith(':') and current_param:
                # Skip other RST directives for now
                pass
            elif current_param and line:
                # Append to current parameter description
                if 'description' not in params_doc[current_param]:
                    params_doc[current_param]['description'] = line
                else:
                    params_doc[current_param]['description'] += '\n' + line
        
        # Build parameter documentation
        parameters = []
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
                
            param_doc = params_doc.get(name, {})
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            
            if hasattr(param_type, '__name__'):
                type_name = param_type.__name__
            elif hasattr(param_type, '__origin__'):
                type_name = str(param_type)
            else:
                type_name = 'Any'
            
            parameters.append(ParameterDocumentation(
                name=name,
                type=type_name,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None,
                description=param_doc.get('description', '')
            ))
        
        # Get return type documentation
        return_type = sig.return_annotation
        return_doc = None
        
        if return_type != inspect.Signature.empty:
            if hasattr(return_type, '__name__'):
                return_type_name = return_type.__name__
            elif hasattr(return_type, '__origin__'):
                return_type_name = str(return_type)
            else:
                return_type_name = 'Any'
                
            return_doc = {"type": return_type_name}
        
        # Create tool documentation
        return ToolDocumentation(
            name=tool_func.__name__,
            description=description,
            parameters=parameters,
            returns=return_doc
        )
    
    def document_tool(self, tool_func: callable) -> callable:
        """Decorator to document a tool function.
        
        Args:
            tool_func: The tool function to document
            
        Returns:
            callable: The decorated function
        """
        tool_doc = self.generate_tool_documentation(tool_func)
        self.documentation.tools[tool_func.__name__] = tool_doc
        return tool_func
    
    def get_documentation(self) -> Dict[str, Any]:
        """Get the complete API documentation.
        
        Returns:
            Dict[str, Any]: The API documentation as a dictionary
        """
        # Update generated timestamp
        self.documentation.generated_at = datetime.now(timezone.utc).isoformat()
        return self.documentation.dict()
    
    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generate an OpenAPI schema from the documentation.
        
        Returns:
            Dict[str, Any]: The OpenAPI schema
        """
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {
                "title": self.documentation.title,
                "version": self.documentation.version,
                "description": self.documentation.description,
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add paths for each tool
        for tool_name, tool_doc in self.documentation.tools.items():
            path = f"/tools/{tool_name}"
            
            # Create operation
            operation = {
                "summary": tool_doc.description,
                "description": tool_doc.description,
                "operationId": tool_name,
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": tool_doc.returns or {}
                            }
                        }
                    }
                }
            }
            
            # Add parameters
            if tool_doc.parameters:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                }
                
                for param in tool_doc.parameters:
                    param_schema = {
                        "type": param.type.lower() if isinstance(param.type, str) else "string",
                        "description": param.description
                    }
                    
                    if param.default is not None:
                        param_schema["default"] = param.default
                    
                    operation["requestBody"]["content"]["application/json"]["schema"]["properties"][param.name] = param_schema
                    
                    if param.required:
                        operation["requestBody"]["content"]["application/json"]["schema"]["required"].append(param.name)
            
            # Add the operation to the path
            openapi_schema["paths"][path] = {
                "post": operation
            }
        
        return openapi_schema

# Create a singleton instance
documentation_manager = DocumentationManager()

def document_tool(tool_func: callable) -> callable:
    """Decorator to document a tool function.
    
    Args:
        tool_func: The tool function to document
        
    Returns:
        callable: The decorated function
    """
    return documentation_manager.document_tool(tool_func)

def get_api_documentation() -> Dict[str, Any]:
    """Get the complete API documentation.
    
    Returns:
        Dict[str, Any]: The API documentation
    """
    return documentation_manager.get_documentation()

def get_openapi_schema() -> Dict[str, Any]:
    """Get the OpenAPI schema for the API.
    
    Returns:
        Dict[str, Any]: The OpenAPI schema
    """
    return documentation_manager.generate_openapi_schema()



