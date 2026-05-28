# Troubleshooting

## VBoxManage not found

**Cause:** VirtualBox not installed or not on PATH.  
**Fix:** Install VirtualBox; set `VBOX_MANAGE_PATH` in Claude config or env. See [CONFIGURATION.md](CONFIGURATION.md).

## Windows Sandbox unavailable

**Cause:** Windows Home, or feature disabled.  
**Fix:** Requires Win11 Pro/Enterprise/Education. Enable optional feature `Containers-DisposableClientVM`.

## Consumer sandbox: winget missing inside guest

**Cause:** Fresh Sandbox may lack Desktop App Installer.  
**Fix:** `Setup-ConsumerSandbox.ps1` bootstraps winget via MSIX; check `Desktop\consumer-sandbox-launch.log`.

## Dev tools present during naked install test

**Cause:** Launched Dev Infra instead of Consumer sandbox.  
**Fix:** Use `Launch-ConsumerSandbox.ps1`, not `Launch-DevInfraSandbox.ps1`.

## `uvx mcpb` fails

**Cause:** mcpb is npm, not PyPI.  
**Fix:** Option A (drag `.mcpb`) or `npx @anthropic-ai/mcpb install ...`

## Port conflicts (10700–10701)

**Cause:** Another fleet webapp using the same ports.  
**Fix:** Stop the other process or run `just kill-all` from repo root.

## MCP tools missing in Claude

**Cause:** `TOOL_MODE=production` exposes portmanteau tools only.  
**Fix:** For full tool surface, set `TOOL_MODE=testing` in env (dev only).

## Server does not appear in Claude Desktop

**Cause:** Malformed `claude_desktop_config.json`.  
**Fix:** Validate JSON; restart Claude Desktop.
