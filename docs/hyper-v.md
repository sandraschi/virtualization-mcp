# Hyper-V

## Requirements

- **Windows 11 Pro, Enterprise, or Education** (Home edition doesn't include Hyper-V)
- **Hyper-V feature enabled** in Windows Features

```powershell
# Enable Hyper-V (Admin):
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

## VM Management

Same UI as VirtualBox — the VMs page shows both providers. Hyper-V VMs have a blue badge.

| Action | How |
|--------|-----|
| List VMs | `GET /api/v1/vms` (includes Hyper-V VMs) |
| Create | Set `provider: "hyperv"` in the create form |
| Start/Stop | Same buttons, routed to Hyper-V via `?provider=hyperv` |
| Pause/Resume | Same as VirtualBox |

## Limitations

Hyper-V support is currently focused on **basic lifecycle** (create, start, stop, pause, resume). Compared to VirtualBox:

| Feature | VirtualBox | Hyper-V |
|---------|-----------|---------|
| Snapshots | ✅ | ❌ |
| Networking | ✅ (NAT, bridged, etc.) | ❌ |
| Console | ✅ (VRDP + VNC) | ❌ |
| ISO attach | ✅ | ❌ |
| Unattended install | ✅ | ❌ |

Hyper-V is best for **lightweight Windows VM management** — if you need advanced features, use VirtualBox.

## Architecture

Hyper-V calls go through PowerShell cmdlets:
```python
# vm_service.py routes to:
hyperv_manager → PowerShell → Hyper-V WMI
```

No VBoxManage needed. Hyper-V operations run in a separate process via `subprocess.run(["powershell", "-Command", ...])`.
