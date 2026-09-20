# BUILD_LOG.md — virtualization-mcp NSIS build record

Running record for Tauri/NSIS builds (fleet NSIS Build Gate requires this file).
Newest entry first.

## 2026-09-20 ~20:30 +02:00 — v1.6.0 release build (SHIPPED)

**Trigger:** Fail-soft VBox init fix + version bump for release.
**Build:** `native/build.ps1` exit 0 after killing stale `virtualization-mcp.exe`
holders (uv-lock os error 32 on first attempt - same gremlin as the backend
restart). Output: `Virtualization MCP_1.6.0_x64-setup.exe` (42.2 MB).
**MCPB:** `dist/virtualization-mcp-v1.6.0.mcpb` (3.3 MB, fresh src twin).
**Release:** tag `v1.6.0` pushed; GitHub release with both assets:
https://github.com/sandraschi/virtualization-mcp/releases/tag/v1.6.0
**Sandbox proof for this release:** VBox-less guest imports clean, all tools
register, server banner (job `naked-virtualization-mcp-20260920_180101`).
Matrix health verdict stays red by architecture (root entry serves MCP, not
the `:10701` dashboard) - entry-point decision still open.

## 2026-09-20 19:15 +02:00 — v1.5.0 NSIS rebuild + CUA smoke (PASS with notes)

**Trigger:** Full session overhaul (sandbox lifecycle, naked-test harness, MCP
bridge) — rebuild to ship current code + prove the installer.

**Pre-build audit (TAURI_PRODUCTION_PITFALLS Phase 1 A–J):**
- A (ports/naming): backend 10701, bundle id `ai.fleet.virtualization-mcp`,
  sidecar `native/resources/virtualization-mcp-backend.exe`, currentUser — PASS
- B (frontend): all fetches via absolute `API_BASE`; hardcoded
  `http://127.0.0.1:10701` (correct value, not env-conditional — noted, not blocking)
- C (backend CORS): tauri.localhost origins present — PASS
- D (run_server.py): no frozen `chdir`, `src` on path, `_strptime` eager — PASS
- E (spec): **fixed pre-build** — added `joserfc/jwk/jwt` (FastMCP 3.4.5 JWT)
  and `_datetime` hiddenimports + `_datetime` eager import (commit `8d0db73`).
  `noarchive=True`, `upx=False`, torch excluded — PASS after fix
- F (Rust spawn): `resources/` resolution, PORT env, `free_port`, spawn log — PASS
- G (lifecycle): `setup()` spawn, `Exit` kill — PASS (`ExitRequested` not
  separately handled — noted)
- H (scripts): `native/build.ps1` frontend-gate → PyInstaller → embed → NSIS,
  stray-exe cleanup, dist staging — PASS
- I (hooks): `windows/hooks.nsh` kills backend+main pre-install/uninstall — PASS
- J (stdio): N/A — Tauri spawns the HTTP backend (`run_server.py`), not MCP stdio

**Build:** `native/build.ps1` exit 0. Frontend `tsc --noEmit` clean, vite
6.79 s. PyInstaller onefile OK. Output:
`native/target/release/bundle/nsis/Virtualization MCP_1.5.0_x64-setup.exe`
(42.2 MB, up from 34.8 MB — joserfc/cachetools/beartype now bundled),
staged to `dist/`.

**CUA smoke** (`scripts/cua-smoke.py`, exit 0, 10/11 phases):
- PASS: silent install, app launch, backend health, window verify,
  screenshots, feature routes, app-log scan, uninstall (exit 0)
- FAIL (soft): **WebView bridge** — OCR of the app window lacks
  `API reachable` (`bridge_ok_text`). Backend is healthy; likely the
  dashboard status element text/probe differs under Tauri. Needs a look.
- Non-fatal: `/api/v1/diagnostics` 404 during checks; nav-walk OCR title
  mismatches (pages clicked, titles not OCR-matched — WebView2 OCR flakiness).
- Residue: `%LOCALAPPDATA%\Virtualization MCP` (125 files, 155 KB, logs/data)
  survives uninstall; registry/Start-menu/processes clean.

**Follow-ups:** WebView bridge text, diagnostics route, uninstall dir cleanup.

## 2026-09-11 — v1.4.0 bundle (prior)

`Virtualization MCP_1.4.0_x64-setup.exe` (34.8 MB). No BUILD_LOG entry was
written at the time (this file created 2026-09-20 per the build gate).
