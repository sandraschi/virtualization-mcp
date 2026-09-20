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

## Naked-test sandbox never boots (empty steps/log)

**Cause:** Relaunch raced the previous sandbox's teardown. The `vmmem`
Hyper-V worker outlives the user-mode processes; a new instance started
while it lingers wedges with zero LogonCommand output.
**Fix:** Fixed 2026-09-20 - dispatch waits for full teardown (worker included),
verifies boot via job-dir markers, retries once, then writes a
`failed_step: "harness"` RESULT. Lingering `vmmemWindowsSandbox` orphans
self-clear; a host reboot clears stubborn ones.

## `uv` not recognized in start.bat (naked PC / sandbox)

**Cause:** `start.ps1` assumes `uv` on PATH.
**Fix:** Add the `Require-Command "uv" "astral-sh.uv"` bootstrap per
`NAKED_PC_INSTALL_STANDARD` §1 and resolve `$uvExe = (Get-Command uv).Source`.

## Backend restart fails after pyproject change (`uv` file lock, os error 32)

**Cause:** `uv sync` cannot replace `.venv\Scripts\<exe>` while a running
MCP-server process holds it.
**Fix:** Stop the `<repo>.exe` processes first, then start the backend.

## POST /mcp 404 on the web backend

**Cause:** Nothing was mounted at `/mcp` (fixed 2026-09-20: FastMCP app
mounted with lifespan; dashboard bridge at `/mcp/tools*`, `/api/mcp/tool`).
**Fix:** Pull latest; restart the `:10701` backend so the mount loads.

## start-bat.log empty in naked-test job dir

**Cause:** The target's `start.ps1` relaunched hidden on `-Headless`,
detaching stdout into the void.
**Fix:** Skip the hidden relaunch when `[Console]::IsOutputRedirected`;
the harness prefers `-NoBrowser` (keeps stdio attached) over `-Headless`.
