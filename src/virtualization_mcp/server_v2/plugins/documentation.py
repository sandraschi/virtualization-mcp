"""
FastMCP 2.11 Standard Documentation Plugin

This plugin provides automated API documentation and schema generation
following the FastMCP 2.11 standard for MCP servers.
"""
import inspect
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, get_type_hints

from fastapi import APIRouter, HTTPException, status
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from virtualization_mcp.server_v2.plugins.base import BasePlugin
from virtualization_mcp.server_v2.plugins import register_plugin

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

class PluginDocumentation(BaseModel):
    """Documentation for a plugin."""
    name: str
    version: str
    description: str
    author: str = ""
    license: str = ""
    endpoints: List[EndpointDocumentation] = []
    models: Dict[str, Dict[str, Any]] = {}
    configuration: Dict[str, Any] = {}
    examples: List[Dict[str, Any]] = []

class APIDocumentation(BaseModel):
    """Complete API documentation following FastMCP 2.11 standard."""
    mcp_version: str = MCP_DOC_VERSION
    schema_version: str = SCHEMA_VERSION
    title: str
    version: str
    description: str
    base_path: str = "/"
    plugins: Dict[str, PluginDocumentation] = {}
    generated_at: str = datetime.now(timezone.utc).isoformat()

@register_plugin("documentation")
class DocumentationPlugin(BasePlugin):
    """
    FastMCP 2.11 Standard Documentation Plugin
    
    Automatically generates and serves API documentation for all registered plugins.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.docs_enabled = config.get("enabled", True)
        self.docs_path = config.get("path", "/docs")
        self.redoc_path = config.get("redoc_path", "/redoc")
        self.openapi_url = config.get("openapi_url", "/openapi.json")
        self.docs_theme = config.get("theme", "swagger")
        self.include_in_schema = config.get("include_in_schema", True)
        
        # Documentation storage
        self.documentation: APIDocumentation = APIDocumentation(
            title=config.get("title", "virtualization-mcp API"),
            version=config.get("version", "1.0.0"),
            description=config.get("description", "virtualization-mcp API Documentation")
        )
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self) -> None:
        """Set up documentation routes."""
        if not self.docs_enabled:
            return
        
        @self.router.get("/openapi.json", include_in_schema=False)
        async def get_openapi_spec() -> Dict[str, Any]:
            """Return the OpenAPI specification."""
            return self.generate_openapi_spec()
        
        @self.router.get("/documentation", include_in_schema=False)
        async def get_documentation() -> Dict[str, Any]:
            """Return the complete API documentation."""
            return self.generate_documentation()
        
        @self.router.get("/plugins/{plugin_name}/documentation", include_in_schema=False)
        async def get_plugin_documentation(plugin_name: str) -> Dict[str, Any]:
            """Return documentation for a specific plugin."""
            if plugin_name not in self.documentation.plugins:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plugin '{plugin_name}' not found"
                )
            return self.documentation.plugins[plugin_name].dict()
    
    def generate_documentation(self) -> Dict[str, Any]:
        """Generate complete API documentation."""
        # This would be populated by scanning registered routes and plugins
        return self.documentation.dict()
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        # This would generate the OpenAPI spec based on registered routes
        return {
            "openapi": "3.0.3",
            "info": {
                "title": self.documentation.title,
                "version": self.documentation.version,
                "description": self.documentation.description
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
    
    def document_plugin(self, plugin: BasePlugin) -> None:
        """
        Document a plugin by analyzing its routes and models.
        
        This should be called for each plugin during initialization.
        """
        plugin_doc = PluginDocumentation(
            name=plugin.__class__.__name__,
            version=getattr(plugin, "__version__", "1.0.0"),
            description=plugin.__doc__ or "",
            configuration={
                k: str(v) if not isinstance(v, (dict, list)) else v 
                for k, v in plugin.config.items()
            }
        )
        
        # Extract documentation from the plugin's router
        for route in plugin.router.routes:
            endpoint_doc = self._document_route(route)
            if endpoint_doc:
                plugin_doc.endpoints.append(endpoint_doc)
        
        # Extract models from the plugin
        plugin_doc.models = self._extract_models(plugin)
        
        # Add to documentation
        self.documentation.plugins[plugin_doc.name] = plugin_doc
    
    def _document_route(self, route) -> Optional[EndpointDocumentation]:
        """Document a single route."""
        # Skip internal routes
        if getattr(route, "include_in_schema", True) is False:
            return None
        
        # Create endpoint documentation
        endpoint_doc = EndpointDocumentation(
            path=route.path,
            methods=[m for m in route.methods if m not in {"HEAD", "OPTIONS"}],
            summary=getattr(route, "summary", ""),
            description=getattr(route, "description", ""),
            tags=getattr(route, "tags", [])
        )
        
        # Extract parameters
        if hasattr(route, "dependant"):
            for param in route.dependant.query_params:
                param_info = self._extract_parameter_info(param)
                if param_info:
                    endpoint_doc.parameters.append(param_info)
            
            for param in route.dependant.path_params:
                param_info = self._extract_parameter_info(param)
                if param_info:
                    endpoint_doc.parameters.append(param_info)
        
        # Extract request and response models
        if hasattr(route, "response_model"):
            endpoint_doc.response_model = self._model_to_schema(route.response_model)
        
        if hasattr(route, "body_field"):
            endpoint_doc.request_model = self._model_to_schema(route.body_field.type_)
        
        return endpoint_doc
    
    def _extract_parameter_info(self, param) -> Optional[ParameterDocumentation]:
        """Extract parameter information from a FastAPI parameter."""
        if not hasattr(param, "field_info"):
            return None
            
        field_info = param.field_info
        
        return ParameterDocumentation(
            name=param.name,
            type=self._get_type_name(param.annotation),
            required=param.required,
            default=field_info.default if hasattr(field_info, "default") else None,
            description=getattr(field_info, "description", ""),
            example=getattr(field_info, "example", None)
        )
    
    def _extract_models(self, plugin: BasePlugin) -> Dict[str, Dict[str, Any]]:
        """Extract Pydantic models from a plugin."""
        models = {}
        
        # Look for Pydantic models in the plugin's module
        for name, obj in inspect.getmembers(plugin.__class__):
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                models[name] = self._model_to_schema(obj)
        
        return models
    
    def _model_to_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert a Pydantic model to an OpenAPI schema."""
        if not inspect.isclass(model) or not issubclass(model, BaseModel):
            return {"type": self._get_type_name(model)}
        
        schema = {
            "title": model.__name__,
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add fields
        for field_name, field in model.__fields__.items():
            field_schema = {
                "type": self._get_type_name(field.type_)
            }
            
            # Add description if available
            if field.field_info.description:
                field_schema["description"] = field.field_info.description
            
            # Add example if available
            if field.field_info.extra.get("example") is not None:
                field_schema["example"] = field.field_info.extra["example"]
            
            # Handle enums
            if hasattr(field.type_, "__origin__") and field.type_.__origin__ is type:
                if issubclass(field.type_.__args__[0], Enum):
                    field_schema["enum"] = [e.value for e in field.type_.__args__[0]]
            
            schema["properties"][field_name] = field_schema
            
            # Add to required if the field is required
            if field.required:
                schema["required"].append(field_name)
        
        return schema
    
    def _get_type_name(self, type_hint) -> str:
        """Convert a Python type to its string representation."""
        if type_hint is type(None):  # noqa: E721
            return "null"
        
        type_name = str(type_hint)
        
        # Simplify common types
        type_mapping = {
            "<class 'str'>": "string",
            "<class 'int'>": "integer",
            "<class 'float'>": "number",
            "<class 'bool'>": "boolean",
            "<class 'list'>": "array",
            "<class 'dict'>": "object"
        }
        
        return type_mapping.get(type_name, type_name)
    
    async def startup(self) -> None:
        """Startup tasks."""
        await super().startup()
        
        # Generate documentation for all registered plugins
        for plugin in self.manager.plugins.values():
            if plugin != self:  # Skip self
                self.document_plugin(plugin)
        
        logger.info("Documentation plugin started")
    
    async def shutdown(self) -> None:
        """Shutdown tasks."""
        await super().shutdown()
        logger.info("Documentation plugin stopped")



