# Minimal MCP Server Implementation

## Overview
This document outlines the minimal implementation approach for the virtualization-mcp server, focusing on simplicity and reliability. The goal is to maintain a working MCP server with the bare minimum code required for Claude Desktop integration.

## Core Principles

1. **Minimal Dependencies**: Only essential dependencies are included
2. **Simple Code**: Straightforward, easy-to-understand implementation
3. **Progressive Enhancement**: Start small, add features incrementally
4. **Reliability**: Focus on stability over features

## File Structure

```
src/
  virtualization-mcp/
    __init__.py     # Package metadata and version
    __main__.py     # Main entry point and tool registration
pyproject.toml      # Package configuration
mcp_config.json     # MCP server configuration
```

## Implementation Details

### Banner Configuration

By default, the MCP server runs with the banner disabled to ensure compatibility with Claude Desktop. To enable the banner for development purposes, set the `VBOX_MCP_DEV=1` environment variable:

```bash
# Run with banner (development)
VBOX_MCP_DEV=1 python -m virtualization-mcp

# Run without banner (production)
python -m virtualization-mcp
```

### 1. __init__.py
```python
"""VirtualBox MCP Server - Minimal Implementation"""
__version__ = "0.1.0"
```

### 2. __main__.py
```python
"""VirtualBox MCP Server - Minimal Entry Point"""

import asyncio
from fastmcp import FastMCP

def main():
    # Create MCP instance
    mcp = FastMCP(name="virtualization-mcp")
    
    # Register a simple hello tool
    @mcp.tool(name="hello", description="A simple hello world tool")
    async def hello(name: str = "World") -> str:
        """Say hello to someone."""
        return f"Hello, {name}! This is virtualization-mcp."
    
    # Run the MCP server with stdio transport
    asyncio.run(mcp.run(transport="stdio"))

if __name__ == "__main__":
    main()
```

### 3. pyproject.toml
```toml
[build-system]
requires = ["setuptools>=65.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "virtualization-mcp"
version = "0.1.0"
description = "VirtualBox MCP Server for Claude Desktop"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

dependencies = [
    "fastmcp>=2.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=22.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
virtualization-mcp = "virtualization-mcp.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
```

### 4. mcp_config.json
```json
{
  "name": "virtualization-mcp",
  "version": "0.1.0",
  "description": "VirtualBox MCP Server for Claude Desktop",
  "mcpServers": {
    "virtualization-mcp": {
      "command": "python",
      "args": ["-m", "virtualization-mcp"],
      "env": {
        "PYTHONPATH": "./src"
      }
    }
  }
}
```

## Development Workflow

1. **Install in development mode**:
   ```bash
   pip install -e .
   ```

2. **Run the server**:
   ```bash
   python -m virtualization-mcp
   ```

3. **Test in Claude Desktop**:
   - Ensure `mcp_config.json` is in the project root
   - Start Claude Desktop
   - The "hello" tool should be available

## Adding New Tools

1. Add a new tool function in `__main__.py`
2. Decorate it with `@mcp.tool()`
3. Test the tool in Claude Desktop

Example:
```python
@mcp.tool(name="list_vms", description="List all VMs")
async def list_vms() -> list[str]:
    """Return a list of all VMs."""
    return ["vm1", "vm2", "vm3"]
```

## Troubleshooting

1. **Server Not Starting**:
   - Check Python path and dependencies
   - Verify `mcp_config.json` is in the project root
   - Check for port conflicts

2. **Tools Not Appearing**:
   - Ensure tools are registered before `mcp.run()`
   - Check for errors in the server logs
   - Verify tool names are unique

3. **Connection Issues**:
   - Check Claude Desktop logs
   - Verify MCP server is running
   - Ensure correct transport (stdio) is used

## Next Steps

1. Add more VM management tools
2. Implement proper error handling
3. Add logging
4. Add tests
5. Document API endpoints



