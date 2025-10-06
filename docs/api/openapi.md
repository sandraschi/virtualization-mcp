# OpenAPI/Swagger Documentation

## Overview

virtualization-mcp provides comprehensive API documentation using the OpenAPI 3.0 specification, which can be accessed through Swagger UI and ReDoc interfaces.

## Accessing the Documentation

### Swagger UI

Swagger UI provides an interactive interface for exploring and testing the API:

```
http://localhost:8000/docs
```

![Swagger UI](images/swagger-ui.png)

#### Features

- Interactive API documentation
- Try-it-out functionality for testing endpoints
- Model schemas with examples
- Authentication configuration
- Request/response validation

### ReDoc

ReDoc offers an alternative documentation interface with a focus on readability:

```
http://localhost:8000/redoc
```

![ReDoc](images/redoc.png)

#### Features

- Clean, responsive design
- Sidebar navigation
- Request/response examples
- Schema documentation
- Search functionality

## OpenAPI Specification

The raw OpenAPI specification is available at:

```
http://localhost:8000/openapi.json
```

This specification can be used with various API tools, including:

- Postman
- Insomnia
- Swagger Codegen
- OpenAPI Generator

## Authentication in Swagger UI

To authenticate in Swagger UI:

1. Click the "Authorize" button
2. Enter your API key or OAuth2 credentials
3. Click "Authorize"
4. All subsequent requests will include the authentication token

## Customizing the Documentation

### API Metadata

You can customize the API information in your FastAPI application:

```python
app = FastAPI(
    title="virtualization-mcp API",
    description="Comprehensive API for managing virtual machines and containers",
    version="1.0.0",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

### Tags and Descriptions

Use Python docstrings and the `tags` parameter to organize your API:

```python
@app.get("/vms/", tags=["Virtual Machines"])
async def list_vms():
    """
    List all virtual machines.
    
    Returns a paginated list of virtual machines with their current status.
    """
    return {"vms": []}
```

### Request/Response Examples

Add examples to your request and response models:

```python
class VMCreate(BaseModel):
    name: str = Field(..., example="my-vm")
    memory_mb: int = Field(..., example=4096)
    cpu_cores: int = Field(..., example=2)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "production-web-server",
                "memory_mb": 8192,
                "cpu_cores": 4
            }
        }
```

## Documenting Authentication

Document your authentication methods:

```python
app = FastAPI()

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.openapi_schema = {
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter JWT token in the format: Bearer <token>"
            },
            "apiKey": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
                "description": "Enter your API key"
            }
        }
    },
    "security": [{"bearerAuth": []}]
}
```

## Adding Examples

Add detailed examples to your endpoints:

```python
from fastapi import Body

@app.post("/vms/", 
    response_model=VM,
    responses={
        201: {
            "description": "Successfully created a new VM",
            "content": {
                "application/json": {
                    "example": {
                        "id": "vm-12345",
                        "name": "web-server-01",
                        "status": "running",
                        "created_at": "2025-08-01T22:42:33Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid VM configuration"
                    }
                }
            }
        }
    }
)
async def create_vm(vm: VMCreate = Body(
    ...,
    example={
        "name": "web-server-01",
        "memory_mb": 4096,
        "cpu_cores": 2
    }
)):
    return {"id": "vm-12345", "name": vm.name}
```

## Documenting WebSockets

Document WebSocket endpoints:

```python
@app.websocket("/ws/status/{vm_id}")
async def websocket_vm_status(
    websocket: WebSocket,
    vm_id: str,
    token: str = Query(..., description="Authentication token")
):
    """
    WebSocket endpoint for real-time VM status updates.
    
    Sends status updates whenever the VM state changes.
    """
    await websocket.accept()
    # WebSocket logic here
```

## Generating Client Libraries

You can generate client libraries from the OpenAPI specification using:

### OpenAPI Generator

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate TypeScript client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-axios -o ./client

# Generate Python client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o ./python-client
```

### Swagger Codegen

```bash
# Generate Java client
java -jar swagger-codegen-cli.jar generate \
  -i http://localhost:8000/openapi.json \
  -l java \
  -o ./java-client
```

## Best Practices

1. **Keep Documentation Updated**: Update docstrings and examples when changing the API
2. **Use Descriptive Names**: Choose clear, consistent names for paths and parameters
3. **Provide Examples**: Include realistic examples for all endpoints
4. **Document Errors**: Document all possible error responses
5. **Version Your API**: Use URL versioning for breaking changes
6. **Use Standard Status Codes**: Follow HTTP status code conventions
7. **Document Authentication**: Clearly explain how to authenticate
8. **Include Rate Limits**: Document any rate limiting
9. **Use Enums**: For fixed sets of values, use enums instead of strings
10. **Test Your Documentation**: Verify that all examples work as expected



