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

Hyper-V support is focused on **basic lifecycle operations**. Advanced VirtualBox features are not available for Hyper-V:

| Feature | VirtualBox | Hyper-V |
|---------|-----------|---------|
| Create / Start / Stop | ✅ | ✅ |
| Pause / Resume | ✅ | ✅ |
| Delete | ✅ | ✅ |
| Snapshots | ✅ | ❌ |
| Network config (NAT, bridged, etc.) | ✅ | ❌ (uses default switch) |
| Console (VNC / VRDP) | ✅ | ❌ |
| ISO attach / detach | ✅ | ❌ |
| Unattended install | ✅ | ❌ |
| Port forwarding | ✅ | ❌ |
| Templates | ✅ | ❌ |

Hyper-V is ideal for:
- **Lightweight Windows dev VMs** that just need to exist and run
- **Quick testing** where you don't need snapshot rollback or console access
- **Leveraging Windows-native virtualization** without installing VirtualBox

If you need snapshots, console access, advanced networking, or ISO management, use VirtualBox instead — both providers coexist on the same machine.

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
