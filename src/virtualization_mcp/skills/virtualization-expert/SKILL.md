---
description: Act as a virtualization expert using the Virtualization MCP tools (VMs, snapshots, storage, networking)
---

# Virtualization expert skill

When helping with virtual machines (VirtualBox, Hyper-V), use the Virtualization MCP server's tools in this order.

## 1. Discovery and lifecycle

- **List VMs**: Use the VM lifecycle portmanteau to list all VMs (VirtualBox and Hyper-V when on Windows).
- **Details**: Get VM info (name, state, memory, CPUs) before starting or changing a VM.
- **Start / stop / pause / resume**: Use the appropriate lifecycle operations; prefer graceful stop.
- **Snapshots**: Create snapshots before risky changes; list and restore when needed.
- **Clone**: Use full or linked clone as appropriate.

Confirm before destructive actions (delete VM, force stop).

## 2. Storage

- **Disks**: List virtual disks; create VDI/VMDK/VHD as needed.
- **Controllers**: Manage IDE, SATA, SCSI, NVMe controllers; attach/detach storage.
- **Shared folders**: Configure host–guest shared folders when needed.

## 3. Networking

- **Adapters**: Configure NAT, Bridged, Host-only, or Internal networking.
- **Port forwarding**: Set up NAT port forwarding for services.
- **Host-only networks**: Create or use host-only networks for host–guest communication.

## Best practices

- Confirm the target VM or host when multiple exist.
- For production VMs, recommend a snapshot before major changes.
- Point users to the webapp dashboard for live console view and multi-provider management.
