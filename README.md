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

## A Brief History of Virtual Machines

Virtual machines are older than you think. The concept dates to the **1960s**, driven by a problem that still sounds familiar: expensive hardware that was mostly idle.

### Mainframe era (1960s–1970s)

IBM pioneered virtualization on the **IBM System/360-67** (1966) and later the **System/370** (1972). The CP/CMS operating system (precursor to VM/370) introduced the idea of a **hypervisor** — a thin layer that partitions physical hardware into isolated "virtual machines," each running its own OS. This was pure pragmatism: a mainframe cost millions and ran batch jobs at night. Virtualization let multiple research teams share the machine concurrently without stepping on each other.

IBM's **VM/370** became the production version, and its design — a privileged "control program" managing guest operating systems — is the direct ancestor of every Type-1 hypervisor today. The term "virtual machine" itself comes from this era.

### The x86 dark ages (1980s–1990s)

When computing moved from mainframes to x86 workstations and servers, virtualization was essentially lost. The x86 architecture had no concept of privilege rings that could trap and emulate guest OS instructions efficiently. The few attempts (like **VMware Workstation 1.0 in 1999**) used **binary translation** — dynamically rewriting guest instructions on the fly — which was slow and fragile but proved it could be done.

Intel and AMD eventually added hardware virtualization extensions: **Intel VT-x** (2005) and **AMD-V** (2006). These introduced a new "root mode" that lets the CPU natively execute guest instructions without binary translation. This was the unlock that made x86 virtualization performant enough for production.

### The golden age (2005–2015)

With hardware assist in place, virtualization exploded:

- **VMware** dominated the enterprise with ESX/vSphere, building a multi-billion-dollar business on server consolidation (replacing 10 underutilized physical servers with 1 host running 10 VMs).
- **Xen** (2003, Cambridge University) became the open-source standard, powering early AWS (EC2 ran on Xen until 2017). Amazon chose Xen because it was free and could be customized for multi-tenant isolation at scale.
- **KVM** (2007, Avi Kivity/Qumranet) turned Linux itself into a Type-1 hypervisor by adding the `kvm` kernel module. Red Hat acquired Qumranet in 2008 and made KVM the default for RHEV and OpenStack. KVM is now the most widely deployed hypervisor on the planet by sheer host count (every Android phone runs a KVM-based protected VM for Trusty/AVB, every Chromebook runs KVM for Linux containers, every major public cloud uses KVM or a derivative).
- **VirtualBox** (2007, Sun Microsystems, later Oracle) targeted the desktop and developer market — free, cross-platform, easy to use. It never aimed at the datacenter but became the de-facto standard for "I need a VM on my laptop."
- **Hyper-V** (2008, Microsoft) was Microsoft's response, a Type-1 hypervisor built into Windows Server and later Windows Pro/Enterprise. It competed with VMware on Windows workloads and came free with the OS.
- **Parallels** started as a Windows/Linux desktop hypervisor (Parallels Workstation, 2005) but pivoted hard to macOS after acquiring the Mac code in 2006. **Parallels Desktop for Mac** became the dominant solution for running Windows VMs on Apple hardware — first on Intel Macs via full virtualization, then on Apple Silicon via a custom hypervisor that translates x86 to ARM on the fly (Rosetta-like). There is also **Parallels RAS** (Remote Application Server), an enterprise product for virtual app delivery on Windows Server, but it is a much smaller business than the desktop Mac product. The Linux/Windows Workstation versions were discontinued in the early 2010s. Effectively: **Parallels is macOS-only today**, and its sole market is "run Windows on a Mac."

### The cloud and container correction (2015–present)

The rise of AWS, Azure, and GCP changed the question from "which hypervisor do I install?" to "which API do I call?" Nobody cared whether EC2 ran on Xen or KVM (it's KVM now) — they cared about the `RunInstances` API.

Containers (Docker, 2013) then questioned whether full VMs were needed at all. Why run a whole OS when a process-level sandbox with cgroups and namespaces was faster and lighter? Kubernetes (2014) orchestrated containers at scale, and for a while it seemed like VMs were legacy.

But containers don't actually replace VMs — they run on top of them. Every Kubernetes node is a VM (or bare metal, but mostly VMs in the cloud). The two technologies are complementary, not competing. The industry settled on: **containers for application packaging, VMs for isolation and infrastructure.**

### The present (2026)

Today's landscape is stratified:

- **Public cloud** — AWS Nitro (KVM-based with custom silicon), Azure (Hyper-V), GCP (KVM). Customers consume VMs through APIs, never touching a hypervisor.
- **Enterprise on-prem** — VMware (declining post-Broadcom), Hyper-V, Nutanix AHV, Proxmox VE (rising). The Broadcom VMware disaster accelerated a migration wave that will take years to play out.
- **Developer laptops** — VirtualBox, Hyper-V (via Docker Desktop/WSL2), Parallels (macOS), UTM (Apple Silicon QEMU), and Multipass (Canonical's lightweight Ubuntu VMs). The trend is toward lightweight, API-driven VMs that can be provisioned in seconds and discarded just as fast.
- **Edge / IoT** — k3s (Kubernetes on VMs or bare metal), KVM-on-arm (Raspberry Pi 5 can run VMs now), and embedded hypervisors like Jailhouse and ACRN.

This project sits in the developer laptop and edge segment — managing VirtualBox and Hyper-V VMs, Windows Sandbox ephemeral environments, and Docker sandbox containers, all from a unified MCP tool surface. It's a pragmatic snapshot of the 2026 virtualization landscape: free tools, local execution, API-driven, AI-friendly.

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

### Nutanix AHV (Nutanix)
**Status: ❌ Not supported — enterprise scope**

Nutanix AHV is a Type-1 hypervisor built into the Nutanix Acropolis hyperconverged infrastructure (HCI) platform. It is proprietary, licensed per-node as part of the Nutanix AOS/Prism bundle. AHV is KVM-based under the hood but managed exclusively through Nutanix Prism (UI and REST API). It competes with VMware vSphere in the enterprise HCI space and has been a major beneficiary of the Broadcom VMware exodus.

Reasons not currently supported:
- Requires a Nutanix cluster — not available to individual developers or small shops
- The Prism REST API is complex and targets infrastructure teams, not ad-hoc VM management
- Licensing is per-node subscription, typically $5k–$20k/node/year depending on bundle
- The open-source KVM layer underneath is not directly accessible when managed by Acropolis

AHV support would make sense for a future "fleet datacenter" tier that targets enterprise Nutanix customers, but it is out of scope for the current single-machine developer workflow.

### OpenStack (OpenInfra Foundation / community)
**Status: ❌ Not supported — DIY complexity**

OpenStack is a set of open-source (Apache 2.0) projects that together provide infrastructure-as-a-service (Compute via Nova, Storage via Cinder/Swift, Networking via Neutron, Identity via Keystone, etc.). It is the de-facto open-source cloud platform, used by massive deployments (OVH, Rackspace, CERN, Walmart) and telcos.

Reasons not currently supported:
- **DIY infrastructure cost:** OpenStack is free software, but operating it requires a cluster of bare-metal hosts, shared storage (Ceph/CEPH or SAN), and at least 3 controller nodes for HA. A minimal production deployment starts at 6–10 physical servers. There is no "OpenStack on a laptop" — even dev environments (DevStack, MicroStack, Kolla) need significant RAM and multiple VMs.
- **Operational complexity:** OpenStack has 30+ core services. Upgrades are painful, networking (Neutron + OVS/OVN) is notoriously brittle, and troubleshooting requires deep knowledge of RabbitMQ, MySQL/Galera, and distributed system internals.
- **Wrong abstraction layer:** This project manages individual VMs and sandboxes on a single Windows machine. OpenStack is a multi-tenant cloud orchestrator for datacenter-scale deployments. The API surface (Nova boot with flavors, networks, security groups, availability zones) is designed for a cloud operator, not a developer spinning up a single Ubuntu VM.
- **Alternatives exist:** For those who want OpenStack-like capabilities at smaller scale, Proxmox VE provides a similar VM management API with 1% of the operational overhead. We may support Proxmox before OpenStack.

If you are running OpenStack in production and want MCP integration, the right approach is to run a lightweight MCP bridge on your OpenStack controller node that translates MCP tool calls to OpenStack REST API calls (nova, cinder, neutron). That bridge is not part of this repo but could be a separate `openstack-mcp` server.

### Kubernetes (CNCF / community)
**Status: ⚠️ Not directly managed by this server, but adjacent**

Kubernetes is a container orchestration platform that schedules and manages containerized workloads across a cluster of machines. It is not a VM hypervisor — it runs on top of one (Docker, containerd, CRI-O) — but it competes for the same "where do I run my workload?" mindshare.

**Perception vs reality on complexity:**

The conventional wisdom is that Kubernetes is too complex for individual developers. This is true for a manually-configured production cluster with etcd, CNI plugins, ingress controllers, cert-manager, service meshes, monitoring stacks, and persistent storage. Setting that up from scratch is a multi-day slog even for experienced ops teams.

However, the lightweight distributions have changed the calculus significantly:

| Distribution | Install | Footprint | Use case |
|-------------|---------|-----------|----------|
| **k3s** (Rancher) | Single binary, `curl \| sh` | ~50 MB, runs on a Raspberry Pi | Edge, IoT, dev clusters |
| **MicroK8s** (Canonical) | `snap install microk8s` | ~200 MB, includes add-ons | Local dev, CI, offline |
| **kind** (Kubernetes in Docker) | `go install sigs.k8s.io/kind` | Container nodes | CI testing, ephemeral clusters |
| **minikube** | Binary + driver | VM-based (Docker or Hyper-V) | Local development, learning |
| **K3d** (k3s in Docker) | `brew install k3d` | k3s clusters as Docker containers | Dev, CI, multi-node testing |

On a modern machine (16+ GB RAM, SSD), any of these can boot a functional Kubernetes cluster in under 5 minutes. The real time sink was always configuration — picking the right CNI, storage class, ingress, cert management — and this is precisely where AI assistance (Claude, ChatGPT, Codex) shines. An AI agent given "spin up a k3s cluster on this machine with Traefik, Longhorn, and cert-manager" can:
1. Install k3s (one-line curl pipe)
2. Write the Helm values or YAML manifests for each component
3. Apply them in dependency order
4. Verify the cluster is healthy

The total human effort is "type the prompt, review the plan, press enter." The AI handles the five years of Kubernetes tribal knowledge.

**Why it's not directly managed by this server:**

This project manages VMs (VirtualBox, Hyper-V) and sandboxes (Windows Sandbox). Kubernetes is a layer above — it expects a running cluster (on VMs or bare metal) and manages containers within it. The MCP server could expose `kubectl` wrappers (get pods, apply manifests, port-forward), but that is a separate project (`kubernetes-mcp` or similar). The `local-llm-mcp` server in the fleet already uses k3s internally for containerized model serving, proving the lightweight-Kubernetes-on-a-single-machine pattern works in production.

**Bottom line:** Kubernetes is complex, but AI makes the configuration pain disappear. The lightweight distros make the infrastructure cost near-zero. If you need container orchestration alongside VM management, run k3s on the same host and use a separate `kubernetes-mcp` server for `kubectl` access.

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
| **Nutanix AHV** | Proprietary | Per-node subscription | Type-1 | ❌ | ✅ | ❌ | REST API (`Prism`) |
| **OpenStack** | Apache 2.0 | Free (DIY infra cost) | Type-1 (KVM) | ❌ | ✅ | ❌ | REST API (`nova`, `cinder`, `neutron`) |
| **Kubernetes (k3s)** | Apache 2.0 | Free | Orchestrator | ✅ | ✅ | ✅ | `kubectl` / REST API |

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
