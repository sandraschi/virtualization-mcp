# Sandbox assets (reuse folder)

## Dev infra (winget + git, gh, npm, Python, ruff, just, biome)

No large offline bundles required: the script downloads winget from [winget-cli releases](https://github.com/microsoft/winget-cli/releases) and installs tools over the network.

| File | Purpose |
|------|---------|
| `Setup-DevInfraSandbox.ps1` | Run inside Sandbox (mapped as `C:\Assets`): bootstraps winget, then `winget install` for the stack above. |
| `Run-DevInfra.cmd` | Logon launcher: short delay for `C:\Assets`, runs setup (appends **Desktop\\dev-infra-launch.log**), then opens **Show-DevInfraLog.ps1** in a normal PowerShell window (no Notepad needed in Sandbox). |
| `Show-DevInfraLog.ps1` | Prints the last lines of the launch log in a **`-NoExit`** PowerShell window. |
| `DevInfra.wsb` | Sample Windows Sandbox config. **Edit `<HostFolder>`** if your clone is not at `D:\Dev\repos\virtualization-mcp\assets\sandbox`. |
| `..\scripts\Launch-DevInfraSandbox.ps1` | Host launcher: builds a temp `.wsb` with the correct `HostFolder` for this checkout and starts Sandbox. |

From the repo root (host):

```powershell
.\scripts\Launch-DevInfraSandbox.ps1
```

Or double-click `DevInfra.wsb` after fixing `HostFolder`.

---

## Full dev setup (offline / webapp)

Store the Windows Sandbox full-dev installer files here so you don’t re-download them every time.

**Place these files in this folder** (from [winget-cli Releases](https://github.com/microsoft/winget-cli/releases) → Assets):

- `DesktopAppInstaller_Dependencies.zip` (~93 MB)
- `Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle` (~206 MB)

They are gitignored. Then in the webapp **Full dev setup**, set **Assets folder** to this path, e.g.:

- `D:\Dev\repos\virtualization-mcp\assets\sandbox`

The setup script is written here when you click **Launch with full dev setup**; the sandbox maps this folder to `C:\Assets` and runs the script at logon.
