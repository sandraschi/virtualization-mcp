# Naked-test recipe - design (queued 2026-09-09, not yet implemented)

Goal: one host command that proves a target repo installs on a naked PC:

```powershell
just naked-test REPO=https://github.com/sandraschi/<repo>.git
```

## Flow

1. **Host preflight** (`virtualization-mcp` justfile): WindowsSandbox.exe present;
   kill or reuse singleton sandbox; create job dir `jobs/<repo>-<stamp>/` with
   `spec.json` (repo URL, branch, timeout, steps).
2. **Maps**: `assets/sandbox` -> `C:\Assets` (existing payloads) + job dir ->
   `C:\Job` (write-back for results).
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
   - step 1: run `start.bat` non-interactively, capture exit code + timings.
   - step 2 (if start.bat passed): backend `/health` probe where applicable.
   - write `RESULT.json {repo, branch, steps:[{name, exit, ms}], pass, log_tail}`
     to `C:\Job`, keep full log at `Desktop\naked-test.log`.
4. **Host poll**: wait on `jobs/<repo>-<stamp>/RESULT.json` with timeout,
   print summary, exit nonzero on fail. Sandbox discarded on close (ephemeral).

## Safety

- Sandbox is stock + winget-sourced bits only; ephemeral, no host mutation
  except the job dir. No credentials mapped in. Network on (winget needs it).

## Revive checklist

- [ ] implement `assets/sandbox/Run-NakedTest.cmd` (+ spec.json reader)
- [ ] host `just naked-test REPO=...` recipe (temp .wsb generation, poll loop)
- [ ] live run on Goliath: `just naked-test REPO=...on-ai-takeover...`
      (interactive - confirms Sandbox feature + flow; cannot be done headless)
- [ ] on green: reference as enforcement in NAKED_PC_INSTALL_STANDARD (new
      section 8) and in target repos' INSTALL.md ("verified <date> via naked-test")

## Non-goals

Automated UI clicking inside the sandbox (CUA smoke stays separate) -
installer stdout/exit/health only. Airgap mode stays manual (Full dev path).
