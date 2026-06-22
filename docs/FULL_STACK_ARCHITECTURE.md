# Full Stack Architecture - virtualization-mcp

## Overview

virtualization-mcp now supports a **dual-standard architecture** similar to Vienna Transit:

- **🤖 FastMCP Server** (stdio transport) - For Claude Desktop MCP integration
- **🌐 FastAPI Server** (HTTP transport) - For web UI and REST API

Both servers share the same backend services and can run independently or together.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Shared Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ VM Service   │  │ VBox Manager │  │  Templates   │  │
│  │              │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
           ▲                    ▲
           │                    │
    ┌──────┴──────┐      ┌──────┴──────┐
    │             │      │             │
┌───▼──────┐  ┌───▼──────▼──┐  ┌───▼──────┐
│ FastMCP  │  │   FastAPI   │  │  Web UI  │
│  Server  │  │   Server    │  │  (HTML)  │
│          │  │             │  │          │
│ stdio    │  │    HTTP      │  │  HTTP    │
│ transport│  │   transport  │  │  static  │
└──────────┘  └──────────────┘  └──────────┘
     
     │                │
┌────▼────┐      ┌────▼────┐
│ Claude  │      │ Browser │
│ Desktop │      │  Users  │
└─────────┘      └─────────┘
```

## Transport Standards

### FastMCP Server (stdio)
- **Transport**: stdio (standard input/output)
- **Protocol**: MCP (Model Context Protocol)
- **Clients**: Claude Desktop, MCP Inspector
- **Port**: N/A (uses stdin/stdout)
- **Use Case**: AI assistant integration
- **Entry Point**: `virtualization_mcp.all_tools_server.start_mcp_server()`

### FastAPI Server (HTTP)
- **Transport**: HTTP/WebSocket
- **Protocol**: REST API + WebSocket
- **Clients**: Web browsers, mobile apps, API consumers
- **Port**: 3080 (configurable via `WEB_PORT`)
- **Use Case**: Web UI and API access
- **Entry Point**: `virtualization_mcp.web.app.app`

## Code Sharing Strategy

### Shared Modules
Both servers import from the same modules:

```python
# Shared by both servers
from virtualization_mcp.services.service_manager import get_service_manager
from virtualization_mcp.services.vm_service import VMService
from virtualization_mcp.vbox.manager import VBoxManager
from virtualization_mcp.tools.vm.vm_tools import list_vms, start_vm, stop_vm
```

### Server-Specific Code

**FastMCP Server** (`all_tools_server.py`):
- MCP tool implementations
- Pydantic models for MCP responses
- stdio transport handling
- Portmanteau tools registration

**FastAPI Server** (`web/app.py`):
- REST API endpoints (`/api/vms`, `/api/vms/{name}/start`, etc.)
- WebSocket handlers (for real-time updates)
- HTML templates (`web/templates/index.html`)
- Static file serving

## Running the Servers

### Option 1: MCP Server Only (Claude Desktop)
```powershell
# Set environment variable
$env:SERVER_MODE = "mcp"

# Run MCP server
python -m virtualization_mcp.dual_server
```

Or directly:
```powershell
python -m virtualization_mcp.all_tools_server
```

### Option 2: Web Server Only
```powershell
# Set environment variable
$env:SERVER_MODE = "web"

# Run web server
python -m virtualization_mcp.dual_server
```

Or directly:
```powershell
python -m virtualization_mcp.web.server
```

### Option 3: Both Servers (Dual Mode)
```powershell
# Set environment variable
$env:SERVER_MODE = "dual"

# Run both servers
python -m virtualization_mcp.dual_server
```

This starts:
- FastMCP server in a separate process (stdio)
- FastAPI server in another process (HTTP on port 3080)

### Option 4: Separate Terminals (Recommended for Development)
```powershell
# Terminal 1: MCP server
python -m virtualization_mcp.all_tools_server

# Terminal 2: Web server
python -m virtualization_mcp.web.server
```

## Configuration

### Environment Variables

```powershell
# Server mode: "mcp", "web", or "dual"
$env:SERVER_MODE = "dual"

# Web server port (default: 3080)
$env:WEB_PORT = "3080"

# Web server host (default: 0.0.0.0)
$env:WEB_HOST = "0.0.0.0"

# Log level
$env:LOG_LEVEL = "INFO"
```

### Settings in `config.py`

```python
class Settings:
    # Web server configuration
    WEB_PORT: int = 3080
    HOST: str = "0.0.0.0"
    
    # MCP server uses stdio (no port needed)
    # ...
```

## Web API Endpoints

### VM Management
- `GET /api/vms` - List all VMs
- `GET /api/vms/{name}` - Get VM details
- `POST /api/vms` - Create new VM
- `POST /api/vms/{name}/start` - Start VM
- `POST /api/vms/{name}/stop` - Stop VM
- `DELETE /api/vms/{name}` - Delete VM

### System
- `GET /api/system/info` - Get system information
- `GET /api/health` - Health check

### Web UI
- `GET /` - Main dashboard (HTML)

## WebSocket Support

Real-time updates via WebSocket (when `python-socketio` is installed):

```javascript
// Connect to WebSocket
const socket = io('http://localhost:3080');

// Subscribe to VM status updates
socket.emit('subscribe_vm_status', { vm_name: 'my-vm' });

// Receive updates
socket.on('vm_status', (data) => {
    console.log('VM status:', data);
});
```

## Benefits of Dual Standard

✅ **Separation of Concerns**
- MCP tools optimized for AI assistants
- Web UI optimized for human users
- Different protocols for different use cases

✅ **Code Reuse**
- Same backend logic
- Same VM operations
- Same business logic

✅ **Independent Deployment**
- Can update MCP server without affecting web UI
- Can scale independently
- Different release cycles

✅ **Best of Both Worlds**
- MCP: Natural language AI integration
- FastAPI: Rich web interface with real-time updates

## File Structure

```
virtualization-mcp/
├── src/
│   └── virtualization_mcp/
│       ├── all_tools_server.py      # FastMCP server (stdio)
│       ├── dual_server.py           # Dual launcher
│       ├── web/
│       │   ├── app.py               # FastAPI application
│       │   └── server.py            # Web server launcher
│       ├── services/                # Shared services
│       ├── tools/                   # Shared tools
│       └── vbox/                    # Shared VBox integration
├── web/
│   ├── templates/
│   │   └── index.html              # Web UI dashboard
│   └── static/                     # Static assets (CSS, JS)
└── docs/
    └── FULL_STACK_ARCHITECTURE.md  # This file
```

## Next Steps

1. ✅ MCP server structure created
2. ✅ FastAPI web server created
3. ✅ Web UI dashboard created
4. ✅ Dual launcher implemented
5. ⏳ Add more REST API endpoints
6. ⏳ Implement WebSocket real-time updates
7. ⏳ Add authentication/authorization
8. ⏳ Add database layer for VM metadata
9. ⏳ Create deployment documentation

## Status

**Full Stack Setup: COMPLETE** ✅

- FastMCP server (`all_tools_server.py`) - Ready for stdio transport
- FastAPI server (`web/app.py`) - Ready for HTTP transport
- Web UI (`web/templates/index.html`) - Basic dashboard implemented
- Dual launcher (`dual_server.py`) - Can run both servers
- Shared backend - Both servers use same services



