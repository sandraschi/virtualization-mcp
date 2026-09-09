# NakedTest tab spec (queued 2026-09-09 - implements NAKED_TEST_RECIPE.md)

New tab on `webapp/frontend/src/pages/sandbox.tsx`, reusing existing
spinner / error / preview patterns. No new dependencies.

## UI

- Card `Naked install test` (emerald accent, next to Consumer card):
  - inputs: repo (text, `owner/name` or https URL, required),
    branch (text, default `main`), observe seconds (number, default 90),
    health URL (text, optional, e.g. `http://localhost:10909/health`)
  - button `Start naked test` -> POST, stores `job_id`, starts polling
  - step list: rig / clone / just-list / start - each idle / running /
    pass / fail from GET states below; spinner while `status=running`
  - `<pre>` log tail (`log_tail` array), `Download RESULT.json` link
  - banner on fail: failed step name + note (fail-loud: no auto-retry)

## API contract (implemented in backend `main.py`)

- `POST /api/v1/fleet/naked-test`
  `{repo, branch="main", observe_sec=90, health_url="", memory_in_mb=8192}`
  -> `{success, job_id, repo, branch, run_dir}` (400 bad repo, 500 missing payloads)
- `GET /api/v1/fleet/naked-test/{job_id}`
  -> `{status:"running", files}` until `RESULT.json` lands, then the RESULT
  body + `status:"finished"` (404 unknown job, 400 bad id)

## Polling

- `setInterval` 5s while running; stop on finished/error/unmount.
- Timeout guard: `observe_sec + 600s` host-side, then mark `stale`
  (sandbox may have been closed by hand - singleton constraint).

## Step mapping (RESULT.json -> UI)

`steps[].name` in {rig, clone, just-list, start}; current step = first with
no exit or the running tail; `pass=false` highlights `failed_step` red with
`note`. `log_tail` renders verbatim (ASCII only by construction).

## CUA escalation (phase 2, not this build)

Scripted payload covers `start.bat` + health. GUI-only steps (Tauri wizard,
Claude Desktop drag-drop) need CUA-in-the-box: a follow-up `cua_steps[]`
in spec.json executed by `cua-smoke.py` patterns inside the sandbox, with
screenshots written to `C:\Job` and served the same way. Do NOT make CUA
the default actor - deterministic script first.

## Acceptance

- [ ] tab renders beside Consumer card, inputs validate (repo required)
- [ ] start on `sandraschi/on-ai-takeover` (no start.bat -> clean fail at
      `start` step with note, proving fail-loud path)
- [ ] start on `virtualization-mcp` itself (full pass path)
- [ ] close sandbox mid-run -> poll shows `running`, timeout guard marks stale
- [ ] `biome check` + `tsc --noEmit` green on frontend

## Live-run order (interactive, Goliath)

Backend endpoints first (curl POST/GET), then tab, then the two acceptance
repos. Sandbox feature must be enabled; runs are ephemeral by design.
