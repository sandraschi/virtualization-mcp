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
while it lingers wedges with zero LogonCommand output. Pure-`/F` cleanup
makes it worse: killing the user-mode processes with `/F` orphans `vmmem`
instead of letting it exit.
**Fix:** Fixed 2026-09-20 (dispatch waits for full teardown, verifies boot
via job-dir markers, `failed_step: "harness"` RESULT); hardened 2026-10-26
after two back-to-back wedges in one night (proven 2026-10-26 01:27-07:50):
the just-path preflight now closes gracefully first (no `/F`), then `/F`
leftovers, then VERIFIES `vmmemWindowsSandbox` released the partition and
REFUSES to launch (exit 5, names the PID) instead of wedging. Same
graceful-first order in post-run cleanup. A worker that survives even the
SYSTEM teardown task needs an admin `vmcompute` service restart (or reboot).
Lingering orphans otherwise self-clear; a host reboot clears stubborn ones.

## Naked-test `start` step fails health check although the app booted

**Cause:** The harness probed a dashboard URL for a repo whose root
`start.bat` serves no HTTP (e.g. this repo: root start launches the MCP
server, the dashboard is `webapp\start.ps1`). The fleet-start.config.ps1
derivation guessed a URL that can never return 200.
**Fix:** Pass `health=none` (`just naked-test repo=... health=none`,
`"health_url": "none"` via API/MCP, `none` in the Sandbox page Health URL
box): derivation is skipped and the alive-process gate applies (pass if
the process is still alive at end of window). Proven 2026-10-26: full PASS
on `virtualization-mcp` itself (rig + clone + just-list + start).

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
