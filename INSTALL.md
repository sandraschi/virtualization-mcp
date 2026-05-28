# Installing virtualization-mcp

Control VirtualBox, Hyper-V, and Windows Sandbox from Claude Desktop or Cursor.

## Prerequisites

| Tool | Required for | Install |
|------|--------------|---------|
| **Claude Desktop** | Options A–C | [claude.ai/download](https://claude.ai/download) |
| **Windows 11 Pro+** | Sandbox features | Built into eligible SKUs |
| **VirtualBox 7+** | VM features | [virtualbox.org](https://www.virtualbox.org/) |
| **Git** | Options C, D | `winget install Git.Git` |
| **Python + uv** | Options C, D | `winget install astral-sh.uv` |
| **Node.js** | Option B, webapp | `winget install OpenJS.NodeJS` |

> **Windows:** use [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/).  
> After winget installs, close and reopen PowerShell so PATH updates apply.

---

## Option A — Drag and Drop (Recommended)

1. Open [Releases](https://github.com/sandraschi/virtualization-mcp/releases/latest)
2. Download `virtualization-mcp-*.mcpb` (or build with `just mcpb-pack`)
3. Drag into Claude Desktop (Settings → MCP Servers → Install from file)
4. Set VirtualBox path in the MCPB user config when prompted

Restart Claude Desktop if prompted.

---

## Option B — mcpb CLI

`mcpb` is **not** on PyPI — `uvx mcpb` will fail.

```powershell
winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
# Close and reopen terminal, then:
npx @anthropic-ai/mcpb install https://github.com/sandraschi/virtualization-mcp
```

---

## Option C — Manual Configuration

```powershell
winget install astral-sh.uv --accept-source-agreements --accept-package-agreements
winget install Git.Git --accept-source-agreements --accept-package-agreements
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
uv sync --all-extras
```

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\virtualization-mcp",
        "run",
        "virtualization-mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "VBOX_MANAGE_PATH": "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"
      }
    }
  }
}
```

macOS config path: `~/Library/Application Support/Claude/claude_desktop_config.json`

Restart Claude Desktop.

---

## Option D — Developer Mode

Full webapp dashboard, consumer/dev sandbox launchers, tests:

```powershell
winget install Casey.Just
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
uv sync --all-extras
just
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

### Webapp dashboard

```powershell
.\webapp\start.ps1
```

Frontend: http://localhost:10700 — API: http://localhost:10701

### Nearly naked install testing (fleet)

Validate other repos' `INSTALL.md` without pre-installing dev tools:

```powershell
.\scripts\Launch-ConsumerSandbox.ps1 -InstallClaudeDesktop
```

Dev stack sandbox (wrong baseline for naked tests):

```powershell
.\scripts\Launch-DevInfraSandbox.ps1
```

See [docs/sandbox.md](docs/sandbox.md).

---

## Verify Installation

In Claude Desktop:

> List my VirtualBox VMs.

Or run locally:

```powershell
uv run virtualization-mcp --help
VBoxManage --version
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| VBoxManage not found | Install VirtualBox; set `VBOX_MANAGE_PATH` — [CONFIGURATION.md](docs/CONFIGURATION.md) |
| Sandbox launch fails | Windows 11 Pro+ required; enable Windows Sandbox feature |
| `uvx mcpb` fails | Use Option A or `npx @anthropic-ai/mcpb` |
| Port 10700/10701 in use | Stop other fleet webapps or change ports in config |

Full list: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

*Overview: [README.md](README.md)*
