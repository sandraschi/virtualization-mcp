# Onboarding — virtualization-mcp

## What this is

Manage VirtualBox + Hyper-V VMs, Windows Sandboxes, and Docker sandboxes from
Claude Desktop or the fleet webapp (frontend `:10700`, backend `:10701`).

## What you need (wrappee + accounts)

- **VirtualBox 7+** with `VBoxManage` on PATH (VM features). Download:
  https://www.virtualbox.org/wiki/Downloads
- **Windows 11 Pro/Enterprise/Education** for Hyper-V and Windows Sandbox
  (Home edition: those backends degrade gracefully).
- **No online account or API key required** for core VM features. Optional:
  `PROXMOX_HOST` / `PROXMOX_USER` / `PROXMOX_PASSWORD` for a Proxmox backend,
  LLM provider keys for chat fallback (Ollama on `:11434` preferred, free).

## Money / cost

Core features are free (VirtualBox, Hyper-V, Sandbox ship with Windows).
Cloud LLM fallback keys are pay-as-you-go and optional.

## Sanity check (2 minutes)

1. Start the stack: run `start.ps1` (repo root) or `just start`.
2. Open http://127.0.0.1:10700 — the health dot should turn green.
3. Run `vm_management(action="list")` — expect `{"success": true, ...}` even
   with zero VMs (empty list, not an error).

## Pitfalls

- `VBoxManage` missing: install VirtualBox and reopen the shell (PATH refresh).
- Hyper-V cmdlets need an elevated shell on some hosts.
- First backend boot can take up to 3 minutes (VBox detection); the dashboard
  shows yellow "Starting..." meanwhile — wait, do not instant-fail.
- Frontend calls the backend same-origin (`/api/...` via vite proxy) in the
  browser; only the Tauri desktop build uses `http://127.0.0.1:10701` directly.

## Under-hero status

Until the backend answers `/api/v1/health`, dashboard KPIs are marked MOCK
(sample data) and clear automatically once the live backend connects.
