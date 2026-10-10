# Hyper-V

## Requirements

- **Windows 11 Pro, Enterprise, or Education** — Home edition doesn't include Hyper-V at all
- **Hyper-V feature enabled** in Windows Features
- No VirtualBox or VBoxManage needed — Hyper-V is built into Windows

```powershell
# Enable Hyper-V (Admin, one-time):
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
# Reboot required
```

## VM Management

The main VMs page shows VirtualBox and Hyper-V side by side. Hyper-V VMs are marked with a blue badge.

### Create a Hyper-V VM

From the **Hyper-V** page:
1. Click **Create VM**
2. Set name, RAM (MB), disk (GB)
3. The VM is created with default switch networking (NAT-equivalent)

Via API:
```powershell
POST /api/v1/vms
Content-Type: application/json

{"name": "hyperv-test", "provider": "hyperv", "memory_mb": 4096, "disk_gb": 40}
```

### Start / Stop / Pause / Resume

Same buttons as VirtualBox — the provider is detected from the VM metadata. The backend routes to Hyper-V PowerShell cmdlets automatically.

| Action | Button | API |
|--------|--------|-----|
| Start | ▶ Start | `POST /api/v1/vms/{name}/start?provider=hyperv` |
| Stop | ■ Stop | `POST /api/v1/vms/{name}/stop?provider=hyperv` |
| Pause | ⏸ Pause | `POST /api/v1/vms/{name}/pause?provider=hyperv` |
| Resume | ▶ Resume | `POST /api/v1/vms/{name}/resume?provider=hyperv` |

## Current limitations

Hyper-V now covers the full VMConnect workflow (console, checkpoints, ISO media,
switches). Remaining VirtualBox-only features:

| Feature | VirtualBox | Hyper-V |
|---------|-----------|---------|
| Create / Start / Stop | ✅ | ✅ |
| Pause / Resume | ✅ | ✅ |
| Delete | ✅ | ✅ (`DELETE /api/v1/vms/{name}?provider=hyperv`) |
| Checkpoints | ✅ | ✅ (`Checkpoint-VM`, via snapshot routes with `?provider=hyperv`) |
| Network config | ✅ (NAT/bridged/hostonly) | ✅ (VMSwitch list/create/connect) |
| Console | ✅ (VNC/VRDP in browser) | ✅ (VMConnect: `POST /api/v1/vms/{name}/connect`, Enhanced Session toggle) |
| ISO attach / detach | ✅ | ✅ (`POST /api/v1/vms/{name}/iso-attach`, `/iso-detach`) |
| Unattended install | ✅ | ❌ |
| Port forwarding | ✅ | ❌ |
| Templates | ✅ | ❌ |

Hyper-V is ideal for:
- **Lightweight Windows dev VMs** that just need to exist and run
- **Windows-native virtualization** without installing VirtualBox
- **VMConnect console access** with Enhanced Session Mode (USB, clipboard, resolution)

## Console (VMConnect)

Per https://learn.microsoft.com/en-gb/windows-server/virtualization/hyper-v/virtual-machine-connection:

- Click the plug icon on a VM card, or `POST /api/v1/vms/{name}/connect` to
  best-effort launch `vmconnect.exe localhost <name>` on the backend host.
- `GET /api/v1/vms/{name}/connect` returns the local command
  (`vmconnect.exe <server> <name>` and the `/edit` variant) for remote clients.
- Toggle Enhanced Session Mode from the Hyper-V page header, or
  `GET/POST /api/v1/hyperv/enhanced-session`.
- MCP: `hyperv_management(action="console", vm_name="...")`,
  `hyperv_management(action="enhanced_get")` / `enhanced_set`.

## Checkpoints, switches, ISO

- Checkpoints: expand a VM card (camera icon) or use the snapshot routes with
  `?provider=hyperv`. MCP: `checkpoint_list/create/restore/delete`.
- Switches: `GET/POST /api/v1/hyperv/switches`,
  `POST /api/v1/vms/{name}/network-connect`. MCP: `switch_list/create`, `network_connect`.
- ISO: per-VM card ISO section or `iso-attach` / `iso-detach` routes.
  MCP: `iso_attach` / `iso_detach`.

## Architecture

Hyper-V operations go through PowerShell cmdlets, not VBoxManage:

```
Frontend POST → REST API → vm_service → hyperv_manager → PowerShell → Hyper-V WMI
```

The `hyperv_manager.py` module runs PowerShell commands via `subprocess.run`:
- `Get-VM` — list VMs
- `New-VM` — create VM
- `Start-VM` / `Stop-VM` / `Suspend-VM` / `Resume-VM` — lifecycle
- `Remove-VM` — delete

No VBoxManage, no VirtualBox installation required. Works on any Windows edition that supports Hyper-V.
