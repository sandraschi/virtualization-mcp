# virtualization-mcp — Agent Guide

## Overview

VirtualBox and Hyper-V VM management, Windows Sandbox bringup, snapshots, and fleet install testing via FastMCP 3.2.

## Entry Points

- `uv run virtualization-mcp` → `virtualization_mcp.all_tools_server:main`

## Standards

- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files

- [README.md](README.md) — user overview
- [INSTALL.md](INSTALL.md) — Options A–D
- [CLAUDE.md](CLAUDE.md) — Claude Code context
- `scripts/Launch-ConsumerSandbox.ps1` — nearly naked fleet install tests
- `scripts/Launch-DevInfraSandbox.ps1` — dev stack sandbox

## Quick Ref

```powershell
uv run pytest tests/ -q
just serve
just dev
```

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
