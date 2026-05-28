# virtualization-mcp — Agent Guide

## Overview
VirtualBox & Hyper-V VM management, Docker sandboxing, snapshots, networking and storage via FastMCP 3.2

## Entry Points
- `uv run virtualization-mcp` → `virtualization_mcp.all_tools_server:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `CLAUDE.md` — Claude Code context (if present)
