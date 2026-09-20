# Naked-test recipe - design (implemented 2026-09-11, hardened 2026-09-20)

Goal: one host command that proves a target repo installs on a naked PC:

```powershell
just naked-test repo=https://github.com/sandraschi/<repo>.git
```

## Flow

1. **Host preflight** (`virtualization-mcp` justfile or `POST /api/v1/fleet/naked-test`):
   WindowsSandbox.exe present; create job dir `_sandbox_runs/naked-<repo>-<stamp>/`
   with `spec.json` (repo URL, branch, timeout, health/frontend URLs, `e2e_click`).
   **Singleton lifecycle** (both dispatch paths, since 2026-09-20): terminate the
   previous sandbox, wait up to 60 s for teardown (including the `vmmem`
   Hyper-V worker - relaunching while it lingers wedges with zero LogonCommand
   output), launch, verify boot via job-dir markers within 240 s, retry once,
   else write a `failed_step: "harness"` RESULT instead of a forever-ghost.
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
   - step 3 (opt-in, `e2e_click: true`): full-stack E2E - starts `webapp\start.ps1`,
     waits for the frontend, drives Edge through a generic UIA sidebar walk
     (`Invoke-E2EClick.py`, no OCR), writes `E2E.json` + `e2e-*.png` screenshots.
   - write `RESULT.json {repo, branch, steps:[{name, exit, ms}], pass, log_tail}`
     to `C:\Job`, keep full log at `Desktop\naked-test.log`.
4. **Host poll**: wait on `jobs/<repo>-<stamp>/RESULT.json` with timeout,
   print summary, exit nonzero on fail. Sandbox discarded on close (ephemeral).

## Safety

- Sandbox is stock + winget-sourced bits only; ephemeral, no host mutation
  except the job dir. No credentials mapped in. Network on (winget needs it).

## Revive checklist

- [x] implement `assets/sandbox/Run-NakedTest.cmd` (+ spec.json reader)
- [x] host `just naked-test repo=...` recipe (temp .wsb generation, poll loop)
- [x] FastMCP tool actions (`win_sandbox_naked_test`, `win_sandbox_naked_test_status`, `win_sandbox_naked_test_list`)
- [x] Webapp UI with quick-pick chips and recent runs history (`sandbox.tsx`)
- [x] on green: reference as enforcement in NAKED_PC_INSTALL_STANDARD and in target repos' INSTALL.md

## Non-goals

Airgap mode stays manual (Full dev path). UI clicking is opt-in (`e2e_click`),
not default - installer stdout/exit/health only otherwise.
