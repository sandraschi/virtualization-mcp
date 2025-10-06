# MCP Server Development Guide

This guide documents best practices, lessons learned, and troubleshooting tips for developing MCP (Model Control Protocol) servers, based on our experience with the virtualization-mcp project.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Configuration Management](#configuration-management)
3. [Tool Registration](#tool-registration)
4. [Debugging MCP Servers](#debugging-mcp-servers)
5. [Development Workflow](#development-workflow)
6. [Common Pitfalls](#common-pitfalls)
7. [Testing and Validation](#testing-and-validation)
8. [Performance Considerations](#performance-considerations)

## Project Structure

A well-organized MCP server should follow this structure:

```
virtualization-mcp/
├── src/
│   └── virtualization-mcp/
│       ├── __init__.py         # Package metadata and exports
│       ├── main.py             # Main entry point
│       ├── api/                # API endpoints and routes
│       ├── services/           # Business logic and services
│       ├── models/             # Data models
│       ├── utils/              # Utility functions
│       └── mcp_tools.py        # MCP tool registration
├── tests/                      # Test suite
├── docs/                       # Documentation
├── pyproject.toml              # Project metadata and dependencies
└── mcp_config.json             # MCP server configuration
```

## Configuration Management

### Entry Points

Ensure consistency across all entry point configurations:

1. **pyproject.toml**:
   ```toml
   [project.scripts]
   virtualization-mcp = "virtualization-mcp.main:main"
   ```

2. **mcp_config.json**:
   ```json
   {
     "virtualization-mcp": {
       "command": "python",
       "args": ["-m", "virtualization-mcp.main", "--debug"],
       "env": {
         "PYTHONPATH": "${workspaceFolder}/src"
       }
     }
   }
   ```

### Environment Variables

Use environment variables for configuration:

```python
import os

DEBUG = os.getenv("virtualization-mcp_DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("virtualization-mcp_LOG_LEVEL", "INFO")
```

## Tool Registration

### Basic Tool Registration

```python
@mcp.tool(
    name="example_tool",
    description="Example tool description",
    categories=["category1", "category2"]
)
async def example_tool(param1: str, param2: int = 42) -> dict:
    """Detailed tool documentation.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 42)
        
    Returns:
        dict: Result with status and data
    """
    try:
        # Tool implementation
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return {"status": "error", "message": str(e)}
```

### Tool Discovery

Ensure your MCP server implements these standard tools:

1. `list_tools`: List all available tools
2. `get_tool_info`: Get detailed information about a specific tool
3. `get_tool_schema`: Get JSON schema for a tool's parameters

## Debugging MCP Servers

### Common Issues

1. **No Tools Returned**
   - Verify tool registration occurs before server start
   - Check for exceptions during tool registration
   - Ensure tools are properly decorated with `@mcp.tool`

2. **Import Errors**
   - Check `PYTHONPATH` in `mcp_config.json`
   - Verify all dependencies are installed
   - Look for circular imports

### Logging

Configure comprehensive logging:

```python
import logging
from pathlib import Path

def setup_logging(debug=False):
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "virtualization-mcp.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler, file_handler],
        force=True
    )
```

## Development Workflow

### Local Development

1. Install in development mode:
   ```bash
   pip install -e .
   ```

2. Run with debug logging:
   ```bash
   python -m virtualization-mcp.main --debug
   ```

3. Test tool registration:
   ```bash
   mcp-server list_tools
   ```

### Testing

1. Unit tests:
   ```bash
   python -m pytest tests/unit
   ```

2. Integration tests:
   ```bash
   python -m pytest tests/integration
   ```

## Common Pitfalls

1. **Configuration Mismatches**
   - Keep all entry points in sync
   - Document all configuration options
   - Use environment variables for environment-specific settings

2. **Tool Registration Issues**
   - Tools must be registered before starting the server
   - Avoid circular imports in tool definitions
   - Use absolute imports

3. **Error Handling**
   - Always catch and log exceptions in tools
   - Return consistent error responses
   - Include error codes for programmatic handling

## Testing and Validation

### Unit Tests

Test individual components in isolation:

```python
def test_example_tool():
    # Setup
    test_params = {"param1": "test", "param2": 123}
    
    # Execute
    result = example_tool(**test_params)
    
    # Verify
    assert result["status"] == "success"
    assert "data" in result
```

### Integration Tests

Test the complete system:

```python
async def test_tool_registration():
    mcp = FastMCP(name="test", version="1.0.0")
    register_mcp_tools(mcp)
    
    # Verify tools are registered
    assert "list_tools" in mcp._tools
    assert "get_tool_info" in mcp._tools
```

## Performance Considerations

1. **Resource Management**
   - Use connection pooling for database/API clients
   - Implement proper cleanup in `__del__` or context managers
   - Monitor memory usage in long-running processes

2. **Asynchronous Operations**
   - Use `async/await` for I/O-bound operations
   - Avoid blocking calls in event loop
   - Use thread pools for CPU-bound operations

3. **Caching**
   - Cache expensive operations
   - Invalidate cache on relevant events
   - Use appropriate cache TTLs

## Additional Resources

- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [MCP Protocol Specification](https://modelcontrolprotocol.org/spec)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)

---

*Last Updated: 2025-08-06*



