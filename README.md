# virtualization-mcp

**Spin up VMs, sandboxes, and dev environments — from your AI assistant.**

A Model Context Protocol server that gives your AI (Claude Desktop, Cursor, etc.) direct control over VirtualBox, Hyper-V, and Windows Sandbox. Talk to your VMs, don't click through menus.

```text
"create an Ubuntu VM, attach the 24.04 ISO, boot it, and set up port forwarding"
→ 30 seconds, all through chat
```

## Quick start

```powershell
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
just install
webapp\start.ps1
```

Open `http://localhost:10700` — you'll see your VMs, sandbox launcher, app fleet, and console.

## What you get

| Feature | What it does |
|---------|-------------|
| **VMs** | Create, start, stop, pause, snapshot, delete — VirtualBox & Hyper-V |
| **ISO pipeline** | Download Ubuntu, Debian, Windows, Kali directly into assets/vbox |
| **Console** | VNC browser console via noVNC — see and interact with your VMs |
| **Networking** | NAT, Bridged, Host-Only, port forwarding — configure per VM |
| **Unattended install** | autoinstall.yaml / autounattend.xml with dev tools auto-setup |
| **Templates** | Save VM configs, recreate instantly |
| **Windows Sandbox** | Launch disposable sandbox with full dev stack (winget + pip + npm) |
| **Fleet dashboard** | Health-check and launch all registered MCP webapps |

## Documentation

- [Installation & setup](docs/install.md) — prerequisites, config, start scripts
- [Architecture](docs/architecture.md) — how it all fits together
- [VirtualBox](docs/virtualbox.md) — VM lifecycle, networking, snapshots
- [Hyper-V](docs/hyper-v.md) — Windows-native VM management
- [Windows Sandbox](docs/sandbox.md) — isolated dev environments
- [Usage cases](docs/usage-cases.md) — real workflows and examples

## Requirements

- **Windows 11 Pro/Enterprise/Education** (Hyper-V & Sandbox)
- **VirtualBox 7.0+** with `VBoxManage` in PATH (for VirtualBox features)
- **Python 3.12+** and **Node 20+**
- **Ollama** (optional) — local LLM for the chat feature

## License

MIT — do what you want.
