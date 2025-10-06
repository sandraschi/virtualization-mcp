# FastMCP Inspector Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Usage Guide](#usage-guide)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Introduction

The FastMCP Inspector is a powerful web-based interface for testing and debugging your MCP tools. It provides an interactive environment to:

- Test individual tools with custom parameters
- View detailed request/response information
- Debug errors with stack traces
- Explore API documentation
- Monitor performance metrics

## Quick Start

1. Install FastMCP (if not already installed):
   ```bash
   pip install fastmcp
   ```

2. Start the inspector with your MCP server:
   ```bash
   # From the project root
   fastmcp dev src/vboxmcp/all_tools_server.py
   ```

3. Open the web interface:
   ```
   http://127.0.0.1:6274
   ```

## Features

### Tool Explorer
- Browse all available tools
- View tool documentation and parameters
- Execute tools with custom inputs

### Request/Response Inspector
- View raw request payloads
- See detailed response data
- Inspect HTTP headers and status codes

### Error Debugging
- Detailed error messages
- Stack traces for exceptions
- Request/response logging

### Performance Metrics
- Execution time for each tool
- Memory usage
- Request/response sizes

## Usage Guide

### Testing a Tool
1. Open the tool in the inspector
2. Fill in the required parameters
3. Click "Execute"
4. View results in the response panel

### Debugging Errors
1. Check the error message in the response
2. Expand the error details for stack traces
3. Review the request payload for issues
4. Check server logs for additional context

### Working with Complex Types
- **Dictionaries**: Enter as JSON objects
- **Lists**: Enter as JSON arrays
- **Files**: Use the file upload interface

## Troubleshooting

### Common Issues

#### Inspector Not Starting
- Ensure FastMCP is installed: `pip show fastmcp`
- Check for port conflicts (default: 6274)
- Verify your MCP server starts normally

#### Tools Not Appearing
- Check server logs for import errors
- Ensure tools are properly registered
- Verify the MCP server is running

#### Connection Errors
- Check if the server is running
- Verify the host/port configuration
- Check firewall settings

## Best Practices

### Development Workflow
1. Start the inspector in development mode
2. Test new tools immediately after creation
3. Use the inspector to verify error cases
4. Document tool usage with example requests

### Security Considerations
- Never run the inspector in production
- Be cautious with sensitive data in requests
- Use environment variables for credentials

### Performance Testing
- Monitor execution times
- Test with various input sizes
- Check memory usage with large responses

## Advanced Topics

### Customizing the Inspector
You can customize the inspector's behavior by creating a `fastmcp.toml` configuration file:

```toml
[inspector]
port = 3000  # Custom port
host = "0.0.0.0"  # Bind to all interfaces
debug = true  # Enable debug mode
```

### Integration with IDEs
You can configure your IDE to launch the inspector with custom arguments. For example, in VS Code:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastMCP Inspector",
            "type": "python",
            "request": "launch",
            "module": "fastmcp",
            "args": ["dev", "src/vboxmcp/all_tools_server.py"],
            "console": "integratedTerminal"
        }
    ]
}
```

## Support
For additional help, please refer to:
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [GitHub Issues](https://github.com/your-org/vboxmcp/issues)
- [Community Forum](https://community.example.com)
