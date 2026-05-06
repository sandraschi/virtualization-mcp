# Installation

## Prerequisites

| Tool | Required for | Version |
|------|-------------|---------|
| Python | Backend | 3.12+ |
| Node.js | Frontend | 20+ LTS |
| VirtualBox | VMs (optional) | 7.0+ |
| Ollama | Chat (optional) | latest |
| Just | Automation (optional) | latest |

## Clone & install

```powershell
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
just install
```

This runs:
- `python -m venv .venv && pip install -e .`
- `cd webapp/frontend && npm install`

## Start

```powershell
webapp\start.ps1
```

Opens `http://localhost:10700` (frontend) and `http://localhost:10701` (API).

## Configuration

### API keys

Managed through the Settings UI, not `.env`. Stored at:
```
%LOCALAPPDATA%/virtualization-mcp/keys.json
```

### ISO sources

Edit `config/iso_categories.json` to add/remove downloadable ISOs. Reloads on each request — no restart needed.

### VM templates

User-defined templates are stored at:
```
%LOCALAPPDATA%/virtualization-mcp/templates.json
```

Manage through the Templates button in the VirtualBox page.

## Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 10700 |
| Backend (API) | 10701 |

See [mcp-central-docs/operations/WEBAPP_PORTS.md](https://github.com/sandraschi/mcp-central-docs) for fleet port registry.
