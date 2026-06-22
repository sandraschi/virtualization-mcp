# VirtualBox

## VM Lifecycle

### Create

From the UI: **Create New VM** → pick template → optional ISO → optional network mode.

Templates include:
- `ubuntu-dev` — Ubuntu_64, 4 GB RAM, 25 GB disk, 2 CPU
- `win11-pro` — Windows11_64, 8 GB RAM, 80 GB disk, 4 CPU
- User-defined — create your own via the Templates button

```powershell
# create + attach ISO + boot:
POST /api/v1/vms  {"name":"my-vm","template":"ubuntu-dev","iso_path":"assets/vbox/ubuntu-24.04.iso"}
POST /api/v1/vms/my-vm/start
```

### Start / Stop / Pause / Resume

Buttons on each VM card, or:
```powershell
POST /api/v1/vms/{name}/start
POST /api/v1/vms/{name}/stop
POST /api/v1/vms/{name}/pause
POST /api/v1/vms/{name}/resume
```

### Delete

Deletes the VM and optionally its disk files:
```powershell
DELETE /api/v1/vms/{name}
```

## Snapshots

Create point-in-time snapshots, restore, delete:
```powershell
POST /api/v1/vms/{name}/snapshot  {"snapshot_name":"before-update"}
GET  /api/v1/vms/{name}/snapshots
POST /api/v1/vms/{name}/restore   {"snapshot_name":"before-update"}
POST /api/v1/vms/{name}/delete-snapshot  {"snapshot_name":"before-update"}
```

## Networking

Configure per-VM adapters from the Network panel:

| Mode | When to use |
|------|-------------|
| NAT (default) | VM talks out, host reaches in via port forwarding |
| Bridged | VM gets own IP on the LAN like a real machine |
| Host-Only | Isolated network between host and VMs |
| Internal | VMs talk to each other, no host access |

```powershell
POST /api/v1/vms/{name}/network  {"adapter":1,"mode":"bridged","bridged_if":"Realtek"}
POST /api/v1/vms/{name}/network/port-forwarding  {"name":"ssh","protocol":"tcp","host_port":2222,"guest_port":22}
```

## Console

Real-time VNC console via noVNC (embedded in browser):
```powershell
# Enable VRDE, then open
POST /api/v1/vms/{name}/vrde {"enabled":true}
# Web: /vm/{name}/console
# RDP: GET /api/v1/vms/{name}/rdp
```

## ISO Management

1. **Download** from the ISO tabs (Ubuntu, Debian, Windows, Utilities, Safety)
2. **Attach** to VM via Attach ISO button or create-modal dropdown
3. **Unattended install** via Autoinstall button — generates answer files (autoinstall.yaml / autounattend.xml)

ISOs land in `assets/vbox/` and appear automatically in dropdowns.
