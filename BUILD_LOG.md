# BUILD_LOG.md — virtualization-mcp NSIS build record

Running record for Tauri/NSIS builds (fleet NSIS Build Gate requires this file).
Newest entry first.

## 2026-11-07 ~02:10 +01:00 — v1.7.0 release PREP (VMware create/delete + Hackintosh page)

**Trigger:** `vmware_management` could not create VMs (vmrun has no create
verb; page told users to create VMs manually) + 64-bit Workstation installs
probed as "vmrun not found".
**Changes:** `VmwareManager.create_vm/delete_vm` (.vmx + `.vmdk` via
vmware-vdiskmanager), `create`/`delete` MCP actions, `POST
/api/v1/vmware/create` + `action=delete` + `provider: "vmware"` on
`POST /api/v1/vms`, VMware page New-VM form + delete button, Hackintosh lab
page, versions 1.6.1 -> 1.7.0 (pyproject incl. uv-dynamic fallback,
`__init__.__version__`, root + mcpb manifests, tauri.conf.json,
Cargo.toml/lock), CHANGELOG entry.
**Gates:** `ruff check` + `ruff format --check` clean; `tsc -b` + `vite
build` clean (2260 modules, 6.56s; chunk-size warning pre-existing);
`just test` 700 passed / 191 skipped; `test_app_version_matches_package_version`
re-verified at 1.7.0.
**Blocked:** `just mcpb-pack` fails at step 4 (import isolation) - `uv`
cannot replace `.venv\Scripts\virtualization-mcp.exe`, held by a live MCP
session tree (65452 -> 55112 -> 236792, started 00:59, predates this
session). Same os-error-32 gremlin as the v1.6.0 entry. `uv run` anything
(incl. pytest) hits the same lock; venv-python-direct works. Left running
deliberately - kill the holder tree to proceed.
**Remaining for SHIP:** kill holders -> `just mcpb-pack` -> `just
build-native` -> `just cua-nsis-test` -> local gate -> tag `v1.7.0` + `gh
release create` with both assets.

### 2026-11-07 ~02:30 +01:00 — v1.7.0 mcpb-pack (PASS)

**Trigger:** Stale `virtualization-mcp.exe` holders (65452 -> 55112 -> 236792)
killed with Sandra's go; lock released, dev backend (uvicorn :10701) untouched.
**Pack:** all required checks green - import isolation (v1.7.0 banner,
"VMware management tool registered" in probe log), AST, pollution,
prompts 3371/4002/100, launch check (clean-unpack TCP accept).
Output `dist/virtualization_mcp-v1.7.0.mcpb` (358.6 KB, sha256
f2c9fd9d...) + contract-name copy `dist/virtualization-mcp-1.7.0.mcpb`
(same hash, for the gate/upload name).

### 2026-11-07 ~02:45 +01:00 — v1.7.0 NSIS build (PASS, not yet shipped)

**Trigger:** Release prep continued with Sandra's go after the mcpb-pack.
**Build:** `just build-native` exit 0. Frontend (tsc + vite, 2260 modules),
PyInstaller backend `dist/virtualization-mcp-backend.exe` (38.18 MB),
Tauri NSIS `Virtualization MCP_1.7.0_x64-setup.exe` (40.35 MiB) +
contract-name copy `dist/virtualization-mcp-1.7.0-setup.exe` (same bytes).
**Gate:** `check-release-gate.ps1 -Local -Version 1.7.0` 10/11 PASS -
only `cua-reports/cua-result.json` missing.
**Remaining for SHIP (at that point):** `just cua-nsis-test` -> commit ->
tag `v1.7.0` -> `gh release create` with both contract-named assets.

### 2026-11-07 ~15:05 +01:00 — v1.7.0 CUA smoke (PASS 12/12) + gate (11/11 PASS)

**Trigger:** Sandra watched run #1 right-clicking (context menus), missing
pages, taskbar clicks + chat interruption. Forensics + fixes, vendored to the
fleet template as cua-smoke v17/v18 (commits mcd@c876f0f0, mcd@8ce1d7eb).
**Root causes found (all fixed, all with regression coverage in the script):**
1. Run #1 parsed dict-format nav_routes with pair indexing -> KeyError: 0,
   nav walk never ran (the ": 0" in "X Nav click-through: 0").
2. UIA click_input()/synthetic clicks on WebView2 links intermittently open
   link context menus instead of navigating; OCR-against-sidebar-text could
   not tell a menu from a navigation (label always on screen) and digest-diff
   counted menus as "visible effect" -> systematic false passes. Nav now
   actuates via UIA Invoke only; labels verify against the main panel crop.
3. Sidebar has 15 entries, ~7 visible: below-fold clicks landed on black
   space/taskbar. Now: scrolling discovery (found 6 below-fold pages) +
   scroll-into-view before actuation + in-window guard.
4. Global Escape sprayed into whatever held focus (chat compose interrupted).
   Now: foreground-guarded clicks and Escape; skips + logs when focus is lost.
5. Previous runs never tested the installed app: Tauri sidecar serves
   :10701 but CUA probed :10700 (vite dev server, /api proxied to the dev
   backend) -> all green against the dev stack. Config now probes 10701 +
   freshness probe (request-log 200 = current build) + port-free verify.
**Result:** 15/15 pages navigated (digest-differing screenshots each),
48 backend requests logged during the walk (receipt proof),
cua-result.json all_passed=True, installer sha bound (57750b85a110).
Gate `check-release-gate.ps1 -Local -Version 1.7.0`: 11/11 PASS.
**Remaining for SHIP:** tag `v1.7.0` + `gh release create` with
`virtualization-mcp-1.7.0.mcpb` + `virtualization-mcp-1.7.0-setup.exe`.

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
