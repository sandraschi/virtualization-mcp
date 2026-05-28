# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VBOX_MANAGE_PATH` | Auto-detect | Path to `VBoxManage.exe` |
| `VBOX_VM_FOLDER` / `DEFAULT_VM_FOLDER` | `%USERPROFILE%\VirtualBox VMs` | VM storage |
| `VIRTUALIZATION_MCP_PORT` | `10702` | MCP HTTP/SSE port |
| `WEB_PORT` | `3080` (legacy) / webapp `10701` | API port |
| `DEBUG` | `false` | Verbose logging |
| `LOG_LEVEL` | `INFO` | Python log level |
| `TOOL_MODE` | `production` | `production` (portmanteau) or `testing` (all tools) |
| `ENABLE_CONSOLE_LOGGING` | `true` | stderr log handler |
| `FASTMCP_LOG_LEVEL` | — | FastMCP log level (e.g. `WARNING`) |
| `PYTHONUNBUFFERED` | — | Set to `1` in Claude Desktop config |

Sandbox Docker backend (code execution): `SANDBOX_MEM_LIMIT`, `SANDBOX_CPU_QUOTA`, `SANDBOX_TIMEOUT`.

## Claude Desktop

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\virtualization-mcp", "run", "virtualization-mcp"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "VBOX_MANAGE_PATH": "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"
      }
    }
  }
}
```

Config: `%APPDATA%\Claude\claude_desktop_config.json` (Windows).

## Webapp settings

API keys and templates are stored under:

`%LOCALAPPDATA%\virtualization-mcp\`

See legacy [install.md](install.md) for ISO categories and template JSON paths.

## Related

- [INSTALL.md](../INSTALL.md)
- [sandbox.md](sandbox.md) — consumer vs dev sandbox modes
