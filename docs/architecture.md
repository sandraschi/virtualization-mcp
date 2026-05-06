# Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Frontend     │────▶│  Backend API    │────▶│  VBoxManage     │
│  Vite + React │     │  FastAPI        │     │  (subprocess)   │
│  :10700       │     │  :10701         │     │                 │
└──────────────┘     │                 │     ├─────────────────┤
                     │  vm_service.py  │────▶│  Hyper-V        │
                     │  service_mgr    │     │  (PowerShell)   │
                     │                 │     │                 │
                     │  compat_adapter │     ├─────────────────┤
                     │  vbox_compat    │────▶│  VBoxManage     │
                     │  vm_operations  │     │  (subprocess)   │
                     └─────────────────┘     └─────────────────┘
```

## Layers

### Frontend (`webapp/frontend/`)
React SPA with Tailwind CSS. Pages: Dashboard, VirtualBox, Hyper-V, Sandbox, Console, Chat, Settings, Apps.

### Backend API (`webapp/backend/`)
FastAPI server with REST endpoints. Key modules:

| Module | Responsibility |
|--------|---------------|
| `main.py` | All REST endpoints (VMs, ISO, templates, chat, sandbox, fleet) |
| `vm_service.py` | Business logic, delegates to VirtualBox or Hyper-V |
| `vm_operations.py` | VBoxManage subprocess calls for VM lifecycle |
| `compat_adapter.py` | Compatibility layer wrapping vbox_compat |
| `vbox_compat.py` | Raw VBoxManage subprocess wrapper |

### MCP Server (`src/virtualization_mcp/`)
Runs alongside the REST API. Provides tool definitions for MCP clients (Claude Desktop, Cursor, etc.) with:
- 60+ operations organized in 5 portmanteau tools
- FastMCP 3.1+ prompts and skills

### Data flow

```
User (UI) → REST API → vm_service → vm_operations → VBoxManage
                                          ↘ compat_adapter → vbox_compat → VBoxManage
```

For Hyper-V:
```
User (UI) → REST API → vm_service → hyperv_manager → PowerShell
```

For Sandbox:
```
User (UI) → REST API → main.py → WSB XML generation → WindowsSandbox.exe
```
