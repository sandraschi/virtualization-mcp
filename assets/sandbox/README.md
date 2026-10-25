# Sandbox assets (reuse folder)

Three bringups share `assets/sandbox` and `lib/Winget-Bootstrap.ps1`, each with
its own logon script (see mapping below):

| Bringup | Host launcher | Installs dev tools? | Use |
|---------|---------------|---------------------|-----|
| **Consumer (nearly naked)** | `..\scripts\Launch-ConsumerSandbox.ps1` | **No** — winget bootstrap only | Validate fleet `INSTALL.md` Options A–C |
| **Dev infra** | `..\scripts\Launch-DevInfraSandbox.ps1` | **Yes** — git, gh, node, python, uv, ruff, just, biome | Contributor / Option D smoke tests |
| **Full dev** | Webapp Sandbox page | **Yes** — selectable tool list | Custom / AI-assisted sessions |

---

## Consumer (nearly naked install test)

No dev stack. Bootstraps winget if missing, verifies git/uv/node are absent, writes
`Desktop\consumer-install-test-checklist.txt`. Optional Claude Desktop MSIX fixture.

| File | Purpose |
|------|---------|
| `Setup-ConsumerSandbox.ps1` | Winget bootstrap + baseline check + optional Claude MSIX |
| `Run-Consumer.cmd` | Logon launcher → setup script |
| `Show-ConsumerLog.ps1` | Tail `Desktop\consumer-sandbox-launch.log` |
| `Consumer.wsb` | Sample config (edit `HostFolder`) |
| `..\scripts\Launch-ConsumerSandbox.ps1` | Host launcher (temp `.wsb`) |

From repo root:

```powershell
.\scripts\Launch-ConsumerSandbox.ps1
.\scripts\Launch-ConsumerSandbox.ps1 -InstallClaudeDesktop
.\scripts\Launch-ConsumerSandbox.ps1 -Plain
```

`-Plain` skips logon script (stock sandbox session). Webapp: **WSB: Consumer (nearly naked)** on Sandbox page.

---

## Dev infra (winget + git, gh, npm, Python, ruff, just, biome)

| File | Purpose |
|------|---------|
| `lib/Winget-Bootstrap.ps1` | Shared winget MSIX bootstrap (consumer + dev infra) |
| `Setup-DevInfraSandbox.ps1` | Winget bootstrap, then `winget install` dev stack |
| `Run-DevInfra.cmd` | Logon launcher |
| `Show-DevInfraLog.ps1` | Tail dev-infra log |
| `DevInfra.wsb` | Sample config |
| `..\scripts\Launch-DevInfraSandbox.ps1` | Host launcher |

```powershell
.\scripts\Launch-DevInfraSandbox.ps1
```

---

## Full dev setup (online / webapp)

Three distinct bringups share `assets/sandbox` but run **different** logon scripts:

| Bringup | LogonCommand | WSB sample |
|---------|--------------|------------|
| Dev infra | `C:\Assets\Run-DevInfra.cmd` | `DevInfra.wsb` |
| Consumer | `C:\Assets\Run-Consumer.cmd` | `Consumer.wsb` |
| Full dev | `C:\Assets\Run-DevSetup.cmd` | `FullDev.wsb` |

All three bootstrap winget online if missing (cached under `cache\winget` when
present). The full-dev `Setup-DevSandbox.ps1` checked in here is the canonical
default; the webapp regenerates it from your tool selection on launch.
