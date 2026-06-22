# virtualization-mcp

Spin up VMs, sandboxes, and dev environments from Claude Desktop, Cursor, or the fleet webapp.

<p align="center">
  <a href="https://github.com/sandraschi/virtualization-mcp"><img src="https://img.shields.io/github/stars/sandraschi/virtualization-mcp?style=flat-square" alt="Stars"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

## Features

- **VirtualBox & Hyper-V** — create, start, stop, snapshot, clone VMs
- **Windows Sandbox** — consumer (nearly naked) and dev-infra bringups for fleet install testing
- **ISO pipeline** — download Ubuntu, Debian, Windows ISOs into `assets/vbox`
- **noVNC console** — browser VM console from the webapp
- **Unattended Win11** — autoinstall with optional dev tools (dev VMs only)
- **Fleet dashboard** — health-check and launch registered MCP webapps

## Virtualization Landscape

This project integrates with a deliberately curated set of virtualization backends. Here is the full landscape and why each technology was chosen or rejected.

### VirtualBox 7+ (Oracle, GPLv2)
**Status: ✅ Supported as primary VM backend**

Oracle VM VirtualBox is the default hypervisor for this project. It is free, open-source (GPLv2), runs on Windows/Linux/macOS, and exposes a mature CLI (`VBoxManage`) that covers VM lifecycle, snapshots, networking, storage, VRDP, unattended installs, and more. The `pyvbox` Python API provides direct bindings for Python 3.12. VirtualBox's strength is its zero-cost entry and broad OS compatibility — any developer can install it without a license server or subscription.

| Feature | Via VBoxManage |
|---------|---------------|
| VM lifecycle | `list`, `createvm`, `startvm`, `controlvm`, `unregistervm` |
| Snapshots | `snapshot take/restore/delete` |
| Networking | `hostonlyif`, `natnetwork`, `modifyvm --nic` |
| Storage | `storagectl`, `storageattach` |
| VRDP/remote | `modifyvm --vrde on`, `showvminfo --machinereadable` |
| Unattended install | `unattended install` (VBox 7+) |

### Hyper-V (Microsoft, Windows-only)
**Status: ✅ Supported as secondary VM backend**

Microsoft Hyper-V is a Type-1 hypervisor built into Windows Pro/Enterprise/Education. It is managed via PowerShell (`Get-VM`, `New-VM`, `Start-VM`, etc.) and provides native Windows VM performance with no additional install. Hyper-V is used for Gen2 VMs with UEFI boot and TPM support (required for Windows 11 guest VMs without workarounds).

| Feature | Via PowerShell |
|---------|---------------|
| VM lifecycle | `Get-VM`, `New-VM`, `Start-VM`, `Stop-VM`, `Remove-VM` |
| Generation | Gen1 (BIOS) or Gen2 (UEFI) |
| Limitations | No snapshot API via PowerShell, no VRDP passthrough |

Hyper-V is **not** available on Windows Home edition — the app detects this and degrades gracefully.

### Windows Sandbox (Microsoft, Windows-only)
**Status: ✅ Supported for ephemeral sandbox environments**

Windows Sandbox is a lightweight VM built on Hyper-V technology that provides a disposable, isolated Windows environment. Each launch creates a fresh image from the host's base Windows installation. Changes are discarded when the sandbox closes.

The project supports three sandbox modes:
- **Consumer** — completely naked Windows, no pre-installed tooling. Used for testing install walkthroughs on a simulated "naked PC."
- **Dev Infra** — includes winget, uv, git, and network access. Used for testing fleet deployment scripts and MCP server installs.
- **Full Dev** — user-selectable tooling (Python, Node, VS Code, Cursor, etc.) installed automatically at first boot.

### Docker (Docker Inc.)
**Status: ✅ Partially supported for container execution**

Docker is supported for ephemeral sandbox-style container execution (run isolated commands, compile code, execute scripts) via the `sandbox_management` portmanteau tools. This is not a full Docker Compose or Kubernetes replacement — it is a lightweight "run a command in a throwaway container" feature for development workflows.

### VMware / vSphere (Broadcom, formerly VMware Inc.)
**Status: ❌ Not supported — see below**

VMware was **not selected** for this project. The reasons are both technical and ethical:

**The Broadcom takeover (Nov 2023):** Broadcom completed its $69B acquisition of VMware in November 2023. Within months, Broadcom:
- Terminated all perpetual license sales — customers are forced into subscription-only pricing.
- Bundled products into massive "VMware Cloud Foundation" suites with 2–5× price increases.
- Killed free versions (vSphere Hypervisor, VMware Player for commercial use lost functionality, Workstation Pro was made free only after public backlash in May 2024 — and then Workstation Pro/Fusion Pro were open-sourced in Nov 2024, likely to offload maintenance).
- Laid off thousands of VMware engineers, gutting product teams.
- Imposed punitive audit terms on existing enterprise customers, with some reporting 300–500% renewal cost increases.

**The customer rip-off pattern:** Broadcom's playbook is consistent across acquisitions (CA Technologies, Symantec, VMware):
1. Acquire a critical infrastructure vendor
2. Eliminate perpetual licenses → force subscriptions
3. Bundle products into expensive suites
4. Ratchet prices after lock-in
5. Cut R&D to the bone

For a virtualization management tool like this one, depending on VMware would mean:
- Requiring users to have a paid vSphere/vCenter license (most individual developers don't)
- Being at the mercy of Broadcom's licensing terms and price changes
- Supporting a shrinking ecosystem as customers migrate away

**The post-Broadcom landscape (2024–2026):** The VMware exodus is real. Enterprises are migrating to:
- **Microsoft Hyper-V** (already supported here)
- **Proxmox VE** (open-source KVM-based, growing rapidly)
- **Nutanix AHV** (proprietary but Broadcom-free)
- **Oracle VirtualBox** (already supported here)
- **KVM/libvirt** (Linux-native, open-source)

We may add **Proxmox VE** support in a future release, as it is the most natural open-source replacement for vSphere in the small-to-mid datacenter segment.

### Proxmox VE (Proxmox Server Solutions GmbH)
**Status: 🔜 Under consideration for future support**

Proxmox VE is an open-source (GNU AGPLv3) virtualization platform based on KVM and LXC. It provides a web UI, REST API, clustering, and live migration — similar to vSphere but without the licensing cost. It is the leading candidate for the next hypervisor backend added to this project.

### KVM / libvirt (Red Hat / community)
**Status: 🔍 Under investigation**

KVM (Kernel-based Virtual Machine) is the Linux-native Type-1 hypervisor. It is managed via `libvirt` and `virsh`. Linux-native support would be added if cross-platform parity becomes a priority.

### Comparison Table

| Technology | License | Cost | Type | Windows | Linux | macOS | API |
|-----------|---------|------|------|---------|-------|-------|-----|
| **VirtualBox** | GPLv2 | Free | Type-2 | ✅ | ✅ | ✅ | `VBoxManage` CLI |
| **Hyper-V** | Proprietary | Windows license | Type-1 | ✅ | ❌ | ❌ | PowerShell |
| **Windows Sandbox** | Proprietary | Windows Pro/Ent | Type-1 | ✅ | ❌ | ❌ | WSB XML |
| **Docker** | Apache 2.0 | Free | Container | ✅ | ✅ | ✅ | Docker CLI/API |
| **VMware** | Proprietary | Subscription | Type-1/2 | ✅ | ✅ | ✅ | `govc` / REST API |
| **Proxmox VE** | AGPLv3 | Free | Type-1 | ❌ | ✅ | ❌ | REST API |
| **KVM** | GPLv2 | Free | Type-1 | ❌ | ✅ | ❌ | `virsh` / libvirt |

## Quick Install

1. Download **`virtualization-mcp-*.mcpb`** from [Releases](https://github.com/sandraschi/virtualization-mcp/releases/latest)
2. Drag into **Claude Desktop**

Other methods: **[INSTALL.md](INSTALL.md)**

## What You Can Do

> Create an Ubuntu 24.04 VM with 8 GB RAM and attach the ISO from assets.

> Launch a consumer Windows Sandbox so I can test a naked INSTALL.md walkthrough.

> Restore snapshot clean-base on NakedWin11 before the next install test.

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | Options A–D, sandbox launchers |
| [Configuration](docs/CONFIGURATION.md) | Env vars, VirtualBox paths |
| [Development](docs/DEVELOPMENT.md) | `just`, tests, mcpb build |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors |
| [VirtualBox](docs/virtualbox.md) | VM lifecycle, snapshots |
| [Windows Sandbox](docs/sandbox.md) | Consumer vs dev bringup |
| [Architecture](docs/architecture.md) | System design |

## Requirements

- **Windows 11 Pro/Enterprise/Education** for Hyper-V and Windows Sandbox
- **VirtualBox 7+** with `VBoxManage` on PATH (VM features)
- **Python 3.12+** — only for Options C/D

## License

MIT
