"""
Development Tools for virtualization-mcp

This module provides development and documentation utilities for the virtualization-mcp project.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, get_type_hints


@dataclass
class ParameterDocumentation:
    """Documentation for a function parameter."""

    name: str
    type: str
    description: str = ""
    default: Any = inspect.Parameter.empty
    required: bool = True


@dataclass
class ToolDocumentation:
    """Documentation for a tool/function."""

    name: str
    description: str
    parameters: list[ParameterDocumentation]
    return_type: str
    return_description: str = ""
    examples: list[str] = None

    def to_dict(self) -> dict:
        """Convert the documentation to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "default": param.default if param.default != inspect.Parameter.empty else None,
                    "required": param.required,
                }
                for param in self.parameters
            ],
            "return_type": self.return_type,
            "return_description": self.return_description,
            "examples": self.examples or [],
        }


def document_tool(func: Callable) -> Callable:
    """
    Decorator to document a tool function.

    Args:
        func: The function to document.

    Returns:
        The decorated function with added documentation metadata.
    """
    if not hasattr(func, "__doc__") or not func.__doc__:
        raise ValueError(f"Function {func.__name__} must have a docstring")

    # Parse docstring
    docstring = func.__doc__.strip()
    lines = [line.strip() for line in docstring.split("\n")]

    # Extract description (first non-empty line until first parameter)
    description_lines = []
    for line in lines:
        if line.startswith(":param") or line.startswith(":return"):
            break
        if line:
            description_lines.append(line)

    description = "\n".join(description_lines).strip()

    # Extract parameter docs
    params_docs = {}
    current_param = None

    for line in lines:
        if line.startswith(":param "):
            parts = line[7:].split(":", 1)
            if len(parts) == 2:
                param_name = parts[0].strip()
                param_desc = parts[1].strip()
                params_docs[param_name] = param_desc
                current_param = param_name
        elif line.startswith(":type ") and current_param:
            # Type information can be added to the docstring
            pass

    # Get type hints
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)

    # Build parameter documentation
    parameters = []
    for param_name, param in signature.parameters.items():
        if param_name == "self":
            continue

        param_type = type_hints.get(
            param_name, str(param.annotation) if param.annotation != param.empty else "Any"
        )
        if hasattr(param_type, "__name__"):
            param_type = param_type.__name__

        parameters.append(
            ParameterDocumentation(
                name=param_name,
                type=str(param_type),
                description=params_docs.get(param_name, ""),
                default=param.default if param.default != param.empty else None,
                required=param.default == param.empty,
            )
        )

    # Get return type
    return_type = type_hints.get("return", "None")
    if hasattr(return_type, "__name__"):
        return_type = return_type.__name__

    # Extract return description
    return_desc = ""
    in_return = False
    for line in lines:
        if line.startswith(":return:"):
            return_desc = line[8:].strip()
            in_return = True
        elif in_return and line.strip() and not line.startswith("    "):
            break
        elif in_return and line.strip():
            return_desc += "\n" + line.strip()

    # Create and attach documentation
    func.__tool_docs__ = ToolDocumentation(
        name=func.__name__,
        description=description,
        parameters=parameters,
        return_type=str(return_type),
        return_description=return_desc,
    )

    return func


def get_api_documentation(modules=None) -> dict[str, list[dict]]:
    """
    Generate API documentation for all tools in the specified modules.

    Args:
        modules: List of modules to document. If None, documents all registered tools.

    Returns:
        Dictionary mapping module names to lists of tool documentation.
    """
    import virtualization_mcp.tools as tools

    if modules is None:
        # Get all submodules of virtualization_mcp.tools
        modules = [
            getattr(tools, name)
            for name in dir(tools)
            if not name.startswith("_") and inspect.ismodule(getattr(tools, name))
        ]

    docs = {}

    for module in modules:
        module_name = module.__name__.split(".")[-1]
        module_docs = []

        for _name, obj in inspect.getmembers(module):
            if (inspect.isfunction(obj) or inspect.ismethod(obj)) and hasattr(obj, "__tool_docs__"):
                module_docs.append(obj.__tool_docs__.to_dict())

        if module_docs:
            docs[module_name] = module_docs

    return docs


def get_openapi_schema(title: str = "virtualization-mcp API", version: str = "1.0.0") -> dict:
    """
    Generate an OpenAPI schema for the virtualization-mcp API.

    Args:
        title: The title of the API.
        version: The API version.

    Returns:
        OpenAPI schema as a dictionary.
    """
    docs = get_api_documentation()

    paths = {}
    components = {
        "schemas": {
            "ParameterDocumentation": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "default": {},
                    "required": {"type": "boolean"},
                },
            },
            "ToolDocumentation": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "parameters": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ParameterDocumentation"},
                    },
                    "return_type": {"type": "string"},
                    "return_description": {"type": "string"},
                    "examples": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    }

    for module_name, tools in docs.items():
        for tool in tools:
            path = f"/api/{module_name}/{tool['name']}"
            paths[path] = {
                "post": {
                    "summary": tool["description"].split("\n")[0]
                    if tool["description"]
                    else tool["name"],
                    "description": tool["description"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        param["name"]: {
                                            "type": param["type"].lower()
                                            if isinstance(param["type"], str)
                                            else "string",
                                            "description": param["description"],
                                            "required": param["required"],
                                        }
                                        for param in tool["parameters"]
                                    },
                                    "required": [
                                        param["name"]
                                        for param in tool["parameters"]
                                        if param["required"]
                                    ],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Successful operation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {
                                                "type": tool["return_type"].lower()
                                                if isinstance(tool["return_type"], str)
                                                else "object"
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": "API documentation for virtualization-mcp tools.",
        },
        "paths": paths,
        "components": components,
    }
