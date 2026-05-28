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
