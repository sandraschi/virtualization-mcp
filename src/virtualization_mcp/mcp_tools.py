"""
MCP Tool Discovery and Documentation

This module provides tools for discovering and documenting MCP tools
in a way that's compatible with stdio-based MCP clients like Claude Desktop.
"""

import inspect
from typing import Any

from fastmcp import FastMCP


class MCPToolDiscovery:
    """Handles discovery and documentation of MCP tools."""

    def __init__(self, mcp: FastMCP):
        """Initialize with an MCP instance."""
        self.mcp = mcp
        self.tool_cache = {}

    async def get_tool_info(self, tool_name: str) -> dict[str, Any]:
        """Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool to get info for

        Returns:
            Dictionary containing tool information
        """
        tools = {t.name: t for t in await self.mcp.list_tools()}
        tool = tools.get(tool_name)
        if tool is None:
            return {"error": f"Tool '{tool_name}' not found"}

        tool_func = getattr(tool, "fn", getattr(tool, "func", tool))
        if not callable(tool_func):
            return {"error": f"Tool '{tool_name}' has no function implementation"}

        return self._describe_tool(tool_name, tool_func)

    async def list_tools(self, category: str | None = None, search: str | None = None) -> list[dict[str, Any]]:
        """List all available tools with optional filtering.

        Args:
            category: Filter tools by category
            search: Search term to filter tools

        Returns:
            List of tool information dictionaries
        """
        tools = []
        for tool in await self.mcp.list_tools():
            name = tool.name
            if name.startswith("_"):
                continue
            tool_func = getattr(tool, "fn", getattr(tool, "func", tool))
            if not callable(tool_func):
                continue

            tool_info = self._describe_tool(name, tool_func)

            # Apply filters
            if category and category.lower() not in tool_info.get("categories", []):
                continue

            if search and not self._matches_search(tool_info, search):
                continue

            tools.append(tool_info)

        return tools

    async def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """Get the JSON schema for a tool's parameters.

        Args:
            tool_name: Name of the tool

        Returns:
            JSON schema for the tool's parameters
        """
        tools = {t.name: t for t in await self.mcp.list_tools()}
        tool = tools.get(tool_name)
        if tool is None:
            return {"error": f"Tool '{tool_name}' not found"}

        tool_func = getattr(tool, "fn", getattr(tool, "func", tool))
        if not callable(tool_func):
            return {"error": f"Tool '{tool_name}' has no function implementation"}

        return self._generate_parameter_schema(tool_func)

    def _describe_tool(self, name: str, tool) -> dict[str, Any]:
        """Generate a description dictionary for a tool."""
        func = tool.func
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""

        # Parse docstring
        doc_lines = [line.strip() for line in docstring.split("\n") if line.strip()]
        summary = doc_lines[0] if doc_lines else ""
        description = "\n".join(doc_lines[1:]) if len(doc_lines) > 1 else ""

        # Extract parameter info
        parameters = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_info = {
                "type": self._get_type_name(param.annotation),
                "required": param.default == param.empty,
                "default": param.default if param.default != param.empty else None,
            }

            # Try to extract parameter description from docstring
            param_doc = self._extract_param_doc(param_name, docstring)
            if param_doc:
                param_info["description"] = param_doc

            parameters[param_name] = param_info

        # Build tool info
        tool_info = {
            "name": name,
            "description": summary,
            "long_description": description,
            "parameters": parameters,
            "return_type": self._get_type_name(sig.return_annotation),
            "categories": getattr(tool, "categories", []),
            "requires_auth": getattr(tool, "requires_auth", False),
        }

        # Add endpoint if available (for HTTP compatibility)
        if hasattr(tool, "endpoint"):
            tool_info["endpoint"] = tool.endpoint
            tool_info["method"] = getattr(tool, "method", "GET").lower()

        return tool_info

    def _generate_parameter_schema(self, func) -> dict[str, Any]:
        """Generate a JSON schema for a function's parameters."""
        sig = inspect.signature(func)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            param_schema = {"type": self._get_json_type(param.annotation)}

            if param.default != param.empty:
                param_schema["default"] = param.default
            else:
                required.append(name)

            properties[name] = param_schema

        return {"type": "object", "properties": properties, "required": required}

    @staticmethod
    def _get_type_name(type_obj) -> str:
        """Convert a type object to a string name."""
        if type_obj is inspect.Parameter.empty:
            return "Any"
        return str(type_obj.__name__) if hasattr(type_obj, "__name__") else str(type_obj)

    @staticmethod
    def _get_json_type(python_type) -> str:
        """Map Python types to JSON schema types."""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        if python_type in type_map:
            return type_map[python_type]
        return "string"  # Default to string for unknown types

    @staticmethod
    def _extract_param_doc(param_name: str, docstring: str) -> str | None:
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
    def _matches_search(tool_info: dict[str, Any], search_term: str) -> bool:
        """Check if a tool matches the search term."""
        search_lower = search_term.lower()

        # Search in name, description, and categories
        if (
            search_lower in tool_info["name"].lower()
            or search_lower in tool_info.get("description", "").lower()
            or search_lower in tool_info.get("long_description", "").lower()
            or any(search_lower in cat.lower() for cat in tool_info.get("categories", []))
        ):
            return True

        # Search in parameter names and descriptions
        for param_name, param_info in tool_info.get("parameters", {}).items():
            if search_lower in param_name.lower() or search_lower in param_info.get("description", "").lower():
                return True

        return False


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register MCP tool discovery endpoints.

    Args:
        mcp: The FastMCP instance to register tools with
    """
    # Delegate to the hardened registration path so all entrypoints expose
    # the same contract-quality tools (portmanteau in production mode,
    # plus individual tools in testing mode). See tools/register_tools.py.
    from virtualization_mcp.config import settings
    from virtualization_mcp.tools.register_tools import register_all_tools as register_vbox_tools

    register_vbox_tools(mcp, tool_mode=getattr(settings, "TOOL_MODE", "production"))
