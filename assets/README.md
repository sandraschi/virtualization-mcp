# Assets (reuse folders)

Large or downloaded files used by the webapp and tools live here so they can be reused instead of re-downloaded.

| Folder | Purpose |
|--------|--------|
| **sandbox/** | Windows Sandbox full-dev: `DesktopAppInstaller_Dependencies.zip`, `Microsoft.DesktopAppInstaller_*.msixbundle`. Point the webapp **Assets folder** at `assets/sandbox`. |
| **vbox/** | VirtualBox VM media: ISOs, OVA/OVF images. Point attach/mount ISO or template paths at files in `assets/vbox`. |

All of these files are gitignored. See each folder’s README for what to place there.
