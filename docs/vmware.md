# VMware Workstation Pro backend

Free since Broadcom Nov 2024. Driven via `vmrun -T ws` by `services/vmware_manager.py`.

## Tool

`vmware_management(action=...)`: status, list, get, start, stop, reset, suspend,
pause, unpause, snapshot_list/create/revert/delete, clone, guest_ip.

## Webapp

VMware page calls `GET /api/v1/vmware/status`, `GET /api/v1/vmware/vms`,
`POST /api/v1/vmware/action?action=...`. VMs also appear in `GET /api/v1/vms`
alongside VirtualBox/Hyper-V/Proxmox.

## Env

- `VMWARE_VMRUN_PATH` — explicit vmrun.exe (auto-detected otherwise;
  observed on Goliath: `C:\Program Files\VMware\VMware Workstation\vmrun.exe`)
- `VMWARE_INVENTORY_DIR` — .vmx scan dir (default `~/Documents/Virtual Machines`)

## Download (login vs no-login)

Same binaries either way, no key needed:
- Official (Broadcom login required): https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true
- No-login mirror: https://www.techpowerup.com/download/vmware-workstation-pro/
  (reputable, same official exe). Compare the SHA on the page before running it.

## Hyper-V / WHP coexistence

On Goliath Workstation runs on the Windows Hypervisor Platform (Hyper-V
backend) when VBS/Memory Integrity is on. That works but costs some speed.
For max VMware perf disable Hyper-V/VBS; for side-by-side with Hyper-V VMs
keep WHP and accept the overhead. The manager never toggles this for you.

## macOS note

Best Windows option for macOS slow-tests (Unlocker + smc.version=0 + darwin
guestOS), but Apple-EULA-grey and Unlocker is unofficial. This repo never
downloads Unlocker or macOS images. On Goliath expect CLI `xcodebuild` OK,
Simulator crawling (no Nvidia Metal driver). Use an Intel notebook for daily use.
