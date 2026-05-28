# Development Setup

See [INSTALL.md](../INSTALL.md) Option D for clone and `just` workflow.

## Tools Required

| Tool | Windows | Verify |
|------|---------|--------|
| uv | `winget install astral-sh.uv` | `uv --version` |
| Git | `winget install Git.Git` | `git --version` |
| Node.js | `winget install OpenJS.NodeJS` | `node --version` |
| Just | `winget install Casey.Just` | `just --version` |
| VirtualBox | [virtualbox.org](https://www.virtualbox.org/) | `VBoxManage --version` |

## Setup

```powershell
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
uv sync --all-extras
just
```

## Common Tasks

```powershell
just lint
just test
just serve          # stdio MCP
just dev            # webapp stack
just mcpb-pack      # dist/*.mcpb
```

## Sandbox bringups (host)

```powershell
.\scripts\Launch-ConsumerSandbox.ps1 -InstallClaudeDesktop
.\scripts\Launch-DevInfraSandbox.ps1
```

Consumer = nearly naked (fleet INSTALL.md tests). Dev infra = full dev stack.

## Standards

Fleet doc layout: `mcp-central-docs/standards/README_STRUCTURE.md`
