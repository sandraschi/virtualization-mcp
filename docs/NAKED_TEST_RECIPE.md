# Naked-test recipe - design (implemented 2026-09-11, hardened 2026-09-20)

Goal: one host command that proves a target repo installs on a naked PC:

```powershell
just naked-test repo=https://github.com/sandraschi/<repo>.git
```

## Flow

1. **Host preflight** (`virtualization-mcp` justfile or `POST /api/v1/fleet/naked-test`):
   WindowsSandbox.exe present; create job dir `_sandbox_runs/naked-<repo>-<stamp>/`
   with `spec.json` (repo URL, branch, timeout, health/frontend URLs, `e2e_click`).
   **Singleton lifecycle** (both dispatch paths, hardened 2026-10-25 after shard
   2/4 wedged 22x): serialize on a lock, then the bringdown ladder --
   graceful client close first (same-user WM_CLOSE, no elevation), then
   terminate, kill, taskkill, then the SYSTEM fallback task (see below).
   Teardown is verified BEFORE launch: if the old instance will not die, the
   dispatch refuses to launch (no wedge) and writes a harness RESULT naming
   the leftover PIDs. Boot is verified via job-dir markers within 240 s
   (20 s grace fast-fail when the launcher produced no VM at all), retry once
   only after a clean teardown, else a harness RESULT that distinguishes
   "previous would not die" (host bringdown) from "no boot markers, teardown
   clean" (LogonCommand/assets mapping suspect).
2. **Maps**: `assets/sandbox` -> `C:\Assets` (payloads, incl. `Invoke-E2EClick.py`) +
   job dir -> `C:\Job` (write-back). For local repos a `--bare` mirror is cloned
   to the job dir first so the sandbox tests uncommitted work (`C:\Job\repo.git`).
   The `[remote "origin"]` URL is preferred over any submodule `file://` URL.
3. **Logon**: new payload `Run-NakedTest.cmd` runs at logon:
   - bootstrap winget (`lib/Winget-Bootstrap.ps1`, existing)
   - `winget install git gitHub.cli`? No - minimal rig: **git + just only**.
     Rationale: git is the fetch tool, just is the test runner (like CI).
     Everything else (uv, node, npm, vite, ruff) MUST come from the target
     repo's own `start.bat` Require-Command chain. That is what is under test.
   - `git clone <repo> C:\Test`
   - step 0 (smoke gate): `just --list` in `C:\Test` - on failure STOP, write
     `RESULT.json {pass:false, failed_step:"just-list"}`, done. This is the
     NAKED_PC_INSTALL_STANDARD section 7/7b enforcement arm.
   - step 1: run `start.bat` headless, capture exit code + timings.
     Only switches the target's `start.ps1` declares are passed (`-NoBrowser`
     preferred, `-Headless` fallback - unrecognized switches would fail the run).
     Browsers are opened by Edge executable path, never by URL association
     (fresh sandboxes have no http handler). `start.ps1` files must forward
     args (`... start.ps1 %*`) and must not detach stdout when it is redirected.
    - step 2 (if start.bat passed): backend `/health` probe where applicable.
      Repos whose root `start.bat` serves no HTTP (MCP-server entrypoints
      like this repo - root start launches the MCP server, the dashboard
      lives in `webapp\start.ps1`) pass `health=none` (`just naked-test
      repo=... health=none`, `"health_url": "none"` via API/MCP/UI): the
      fleet-start.config.ps1 derivation is skipped and the harness uses the
      alive-process gate (`start` passes if the process is still alive at
      the end of the observation window).
    - just-path preflight (2026-10-26, after two back-to-back wedges):
      graceful close first (no `/F`, so `vmmem` exits cleanly), then `/F`
      leftovers, then VERIFY `vmmemWindowsSandbox` released the partition
      (up to 60 s). If it lingers, the run refuses to launch (exit 5,
      names the PID) instead of wedging with zero LogonCommand output.
      Same graceful-first order in post-run cleanup so the next run boots
      clean. A stubborn worker still needs the elevated teardown task or
      a `vmcompute` service restart (see Joe-Shmoe step 3 / TROUBLESHOOTING).
   - step 3 (opt-in, `e2e_click: true`): full-stack E2E - starts `webapp\start.ps1`,
     waits for the frontend, drives Edge through a generic UIA sidebar walk
     (`Invoke-E2EClick.py`, no OCR), writes `E2E.json` + `e2e-*.png` screenshots.
   - write `RESULT.json {repo, branch, steps:[{name, exit, ms}], pass, log_tail}`
     to `C:\Job`, keep full log at `Desktop\naked-test.log`.
4. **Host poll**: wait on `jobs/<repo>-<stamp>/RESULT.json` with timeout,
   print summary, exit nonzero on fail. Sandbox discarded on close (ephemeral).

## Run it on your PC (fresh clone - Joe-Shmoe guide)

Works from any clone path, not just `D:\Dev\repos` (the harness sets
`FLEET_REPOS_ROOT` in-guest; the repo's `start.ps1` default only matters for
interactive use).

1. **Windows 11 Pro/Enterprise/Education** with the Sandbox feature (elevated
   once, then reboot):
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -All
   ```
2. **Clone and start the backend:**
   ```powershell
   gh repo clone sandraschi/virtualization-mcp
   Set-Location virtualization-mcp
   .\webapp\start.ps1 -BackendOnly
   ```
   Health: `http://127.0.0.1:10701/health` should return `{"status":"ok"}`.
3. **One-time elevated teardown task** (without it, a wedged `vmmem` worker
   cannot be killed from the medium-integrity backend and the next boot
   wedges - shard 2/4 proved it 22 times). Right-click PowerShell >
   Run as administrator, then:
   ```powershell
   .\scripts\Install-SandboxTeardownTask.ps1
   ```
   Verify from a NORMAL (non-elevated) shell:
   ```powershell
   schtasks /Run /TN virtualization-mcp-sandbox-teardown
   ```
   Expected: `SUCCESS`. The task payload is kill-only on the five Windows
   Sandbox processes. Remove anytime with the `-Uninstall` switch (elevated).
4. **Trigger a test** (any repo, any branch):
    ```powershell
    Invoke-RestMethod -Uri http://127.0.0.1:10701/api/v1/fleet/naked-test `
      -Method Post -ContentType 'application/json' `
      -Body '{"repo": "sandraschi/git-github-mcp"}'
    ```
    Or `just naked-test repo=git-github-mcp` (add `health=none` when the
    target's root `start.bat` serves no HTTP - e.g. MCP-server repos),
    or MCP action `win_sandbox_naked_test` (`health_url: "none"`), or the
    webapp Sandbox page (type `none` in the Health URL box).
   Local checkouts must be committed first - the sandbox tests committed
   HEAD via a bare mirror, and a dirty tree is refused with 409.
5. **Poll** `GET /api/v1/fleet/naked-test/{job_id}` until `status: finished`
   (a run takes ~5-10 min: winget bootstrap + git/just rig, clone,
   `just --list` gate, start observation). Read
   `_sandbox_runs/naked-<repo>-<stamp>/RESULT.json`:
   `{pass, failed_step, note, steps, log_tail}`.
   `failed_step: harness` = host problem (see `note`, it names PIDs);
   anything else (`rig`/`clone`/`just-list`/`start`) = repo problem, fail-loud.

## Safety

- Sandbox is stock + winget-sourced bits only; ephemeral, no host mutation
  except the job dir. No credentials mapped in. Network on (winget needs it).

## Child process logs (repo convention)

`start.bat` output alone rarely explains a red `start` step: backends and
frontends run in separate windows whose text never reaches `start-bat.log`.
Repos with a `start.bat`-launched stack SHOULD redirect child output to
`$repoRoot\logs\<service>.log` (+ `.err.log`), gitignored, windows left
open for live view:

```powershell
$logsDir = Join-Path $repoRoot 'logs'
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
Start-Process powershell.exe -ArgumentList @('-NoProfile', '-NoExit', '-Command', $bCmd) `
    -WorkingDirectory $bWorkDir `
    -RedirectStandardOutput (Join-Path $logsDir 'backend.log') `
    -RedirectStandardError (Join-Path $logsDir 'backend.err.log')
```

The harness exfiltrates `$cloneDir\logs\*` into the host job dir after the
observe window and appends each tail to `start-bat.log`, so the failure
reason shows up in `log_tail`/`RESULT.json` without opening the sandbox.
Missing `logs/` is fine (best-effort) - but then a red `start` step is
opaque. speech-mcp implements this since 2026-10-28 (uv/npm guard fix).

## Revive checklist

- [x] implement `assets/sandbox/Run-NakedTest.cmd` (+ spec.json reader)
- [x] host `just naked-test repo=...` recipe (temp .wsb generation, poll loop)
- [x] FastMCP tool actions (`win_sandbox_naked_test`, `win_sandbox_naked_test_status`, `win_sandbox_naked_test_list`)
- [x] Webapp UI with quick-pick chips and recent runs history (`sandbox.tsx`)
- [x] on green: reference as enforcement in NAKED_PC_INSTALL_STANDARD and in target repos' INSTALL.md

## Non-goals

Airgap mode stays manual (Full dev path). UI clicking is opt-in (`e2e_click`),
not default - installer stdout/exit/health only otherwise.
