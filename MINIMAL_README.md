# Minimal VBoxMCP Server

This is a minimal implementation of the VBoxMCP server focused on FastMCP 2.10+ compatibility and basic functionality.

## Features

- FastMCP 2.10+ compatible server
- Basic stdio transport support
- Single working tool: `list_vms`
- Minimal dependencies

## Requirements

- Python 3.7+
- VirtualBox installed and in PATH
- FastMCP 2.10.0+

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install fastmcp>=2.10.0
   ```

## Running the Server

```bash
# From the src/vboxmcp directory
python -m vboxmcp.minimal_server
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/test_minimal_server.py -v
```

## Usage with Claude Desktop

1. Start the server in a terminal
2. In Claude Desktop, connect to the server via stdio transport
3. Use the available tools:
   ```python
   # List all VMs
   result = await mcp.call("list_vms")
   print(result)
   ```

## Next Steps

- [ ] Add more VM management tools (start, stop, etc.)
- [ ] Implement proper error handling and logging
- [ ] Add configuration options
- [ ] Improve documentation

## License

[Your License Here]
