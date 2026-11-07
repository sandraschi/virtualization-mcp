# Hackintosh lab

Intel notebooks first, Goliath VM only for slow tests.

## Pick hardware

- Best: Intel 8th-10th gen (T490/X1C7, Dell 7390/7400), UHD 620/630, Dortania OpenCore.
- RAM: 16GB floor for Xcode 26, 24-32GB sweet spot. T490 max 40GB (8 soldered + 32).
- Avoid: AMD mobile (sleep/iGPU broken), Snapdragon ARM (no x86 macOS 26), 8GB soldered-only.
- Target macOS 26 Tahoe (last Intel, required for Xcode 26). macOS 27 is ARM-only.

## Get the installer: gibMacOS (direct from Apple, no shady ISOs)

`gibMacOS` (CorpNewt, https://github.com/corpnewt/gibMacOS) downloads macOS
components straight from Apple's `swscan` catalogs. Verified 2026-11-06 on
Goliath: publicrelease catalog lists **macOS Tahoe (25G76)** — that's macOS 26.

```powershell
git clone https://github.com/corpnewt/gibMacOS C:\Temp\gibMacOS
cd C:\Temp\gibMacOS
uv run python gibMacOS.py -c publicrelease
# pick macOS Tahoe (25G76) in the picker, e.g. number 22
```

What lands in `macOS Downloads/`: `InstallAssistant.pkg` chain (Big Sur+
distribution) plus the `.dmg` set. On Windows you get recovery + installer
packages, not a bootable ISO yet — next steps are OpenCore EFI (AMD patches
for 5900X) + building the installer media per Dortania, then attach as ISO
to the VMware VM. Only ever clone from the GitHub URL above (impostor
rehosts exist).

## Goliath slow-test

1. Install VMware Workstation Pro (free, same binaries either way):
   - Official (Broadcom login required): https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true
   - No-login mirror: https://www.techpowerup.com/download/vmware-workstation-pro/ (reputable, same official exe, current 26H1u1 ~600MB). After download, compare the SHA on the page before running it.
2. VMware page green (vmrun found at `C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe`).
2. New VM: 8 vCPU, 16GB, 80GB NVMe, darwin guestOS.
3. Snapshot clean install before Xcode.
4. `xcodebuild` CLI passes, Simulator crawls (4090 has no macOS Metal driver).

## Legal

Apple EULA: virtualised macOS only on Apple hardware. Personal experimentation
only. Unlocker unofficial, unsupported here.
