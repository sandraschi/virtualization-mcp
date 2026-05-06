# Usage cases

## 1. Dev environment in 30 seconds

```text
"Set up an Ubuntu VM with 8 GB RAM, install Python and Docker"
```

1. Create VM from template → attach Ubuntu 24.04 ISO
2. Start VM, the Ubuntu installer runs
3. Post-install, SSH in and install your stack

With unattended install (Autoinstall button), the OS setup is fully automated.

## 2. Test a risky script

```text
"Launch a Windows Sandbox with networking disabled, then test this PowerShell script"
```

1. Open Sandbox page → enable Airgap
2. Launch → script runs in complete isolation
3. Close the sandbox — zero traces on your host

## 3. Snapshot before updates

```text
"Take a snapshot of my dev VM before I run the system update"
```

One click on the VM card → Snapshot. If the update breaks something, restore in one click.

## 4. Multi-VM network lab

```text
"Create three Ubuntu VMs on an internal network so they can talk to each other"
```

1. Create VM1 with network mode Internal Network
2. Create VM2, VM3 with same internal network
3. All three can ping each other, isolated from your LAN

## 5. Automated Windows install

```text
"Create a Windows 11 VM with Python, Git, and VS Code pre-installed"
```

1. Click Autoinstall on the VM card
2. Set username/password
3. Check Python, Git, VS Code in Dev Tools
4. Generate → boots Windows, installs OS, then installs dev tools automatically

## 6. Fleet health check

```text
"Check which MCP servers are running"
```

The Dashboard page shows all registered fleet webapps with live health status. Start any stopped app with one click.

## 7. Windows VM with dev stack

```text
"I need a Windows VM with the full dev environment for testing"
```

1. Create Win11 VM (or use the existing `win11-automated`)
2. Generate autounattend.xml with dev tools checked
3. Attach ISO → boot → Windows installs → dev tools install via winget

Same tooling as the sandbox, but persistent.
