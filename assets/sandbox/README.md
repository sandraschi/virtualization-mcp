# Sandbox assets (reuse folder)

Two bringups share `assets/sandbox` and `lib/Winget-Bootstrap.ps1`:

| Bringup | Script | Installs dev tools? | Use |
|---------|--------|---------------------|-----|
| **Consumer (nearly naked)** | `Launch-ConsumerSandbox.ps1` | **No** — winget bootstrap only | Validate fleet `INSTALL.md` Options A–C |
| **Dev infra** | `Launch-DevInfraSandbox.ps1` | **Yes** — git, gh, node, python, ruff, just, biome | Contributor / Option D smoke tests |
| **Full dev** | webapp offline bundles | **Yes** — selectable tool list | Airgap-capable full stack |

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

## Full dev setup (offline / webapp)

Store winget offline bundles here for full-dev webapp mode. See gitignored assets list in repo `.gitignore`.

The setup script is written here when you click **Launch with full dev setup**; the sandbox maps this folder to `C:\Assets` and runs the script at logon.
