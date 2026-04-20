# virtualization-mcp - Professional Multi-Provider VM Management

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.1.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

**v1.1.0 - Multi-provider virtualization management (VirtualBox & Hyper-V) with advanced lifecycle controls**

> ** Production Ready**: Full-featured VirtualBox management through Claude Desktop with 60+ operations organized in 5 intuitive tools!

[![FastMCP](https://img.shields.io/badge/FastMCP-3.1+-blue)](https://github.com/PrefectHQ/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![VirtualBox](https://img.shields.io/badge/VirtualBox-7.0+-orange)](https://virtualbox.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-499%20passing-brightgreen)](./tests)
[![Coverage](https://img.shields.io/badge/coverage-39%25-yellow)](./coverage.xml)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-black)](https://github.com/astral-sh/ruff)

---

##  What is virtualization-mcp?

virtualization-mcp is a professional Model Context Protocol (MCP) server that brings comprehensive VirtualBox management directly to Claude Desktop. Manage virtual machines using natural language - create, start, stop, snapshot, configure networking, and more!

### Pair with pywinauto-mcp (desktop automation)

**Windows Sandbox** in this server **provisions** a disposable desktop; it does **not** replace **UI automation**. For fleet **safety**, new users who run **pywinauto-mcp** should **also** enable **virtualization-mcp** when they need Sandbox/VM workflows, and run **automation inside the guest**  see **pywinauto-mcp** `docs/SAFETY.md` and **mcp-central-docs** `patterns/PYWINAUTO_MCP_SAFETY.md`.

###  Key Highlights

- ** 5 Portmanteau Tools** - Clean, organized interface with 60+ operations
- ** Switchable Modes** - Production (5 tools) or Testing (60+ tools)
- ** 100% Documented** - Comprehensive docstrings for every operation
- ** 499 Passing Tests** - Robust test suite with 82.5% success rate
- ** 296 KB MCPB** - Optimized package, no bundled dependencies
- ** 8 AI Prompts** - 25+ KB of guidance templates
- ** FastMCP 3.1.0+** - Prompts and skills (virtualization_expert)
- ** Cross-Platform** - Windows, macOS, Linux support

### Prompts and skills (FastMCP 3.1.0)

- **Prompt**: `virtualization_expert`  optional `focus` (general, lifecycle, storage, network). Clients can request this prompt to load instructions so the LLM acts as a virtualization expert using this server's tools.
- **Skill**: Bundled `virtualization-expert` skill in `src/virtualization_mcp/skills/virtualization-expert/SKILL.md`, exposed via `skill://virtualization-expert/SKILL.md` for clients that support MCP resources.
- **Webapp**: The dashboard includes a **Prompts & Skills** page (sidebar) that lists prompts and skills and displays skill markdown; backend serves `GET /api/v1/prompts`, `GET /api/v1/skills`, `GET /api/v1/skills/{id}`.

### Webapp (SOTA dashboard)

- **Frontend**: Port **10700** (Vite). **Backend**: Port **10701** (FastAPI). Run `.\webapp\start.ps1` from repo root.
- **Pages**: Dashboard, VirtualBox, Windows Sandbox, Tools Console, Apps Hub, **Prompts & Skills**, AI Chat, Help, Settings.
- **Windows Sandbox  Full dev setup**: Automated dev stack in Sandbox (winget  Python, Node, uv, Git, Just, VS Code, Notepad++, optional Windsurf/Cursor/Antigravity/Claude Desktop/OpenClaw/OpenFang/RoboFang). **AIRGAP** (no network), optional **host Ollama**. Uses repo **assets/sandbox** for installers; Use repo assets pre-fills the path.
- **VirtualBox  Assets reuse**: Create New VM and Attach ISO use repo **assets/vbox** (ISOs, OVA). Win 11 Pro template; create once from ISO, export to OVA, then import for ready-to-use VM. See [assets/README.md](assets/README.md).
- **API base**: Configured in `webapp/frontend/src/api/config.ts`; override with `VITE_API_URL` if needed.

### Assets (reuse folders)

- **`assets/sandbox/`**  Windows Sandbox full-dev: place `DesktopAppInstaller_Dependencies.zip` and `Microsoft.DesktopAppInstaller_*.msixbundle` (from [winget-cli Releases](https://github.com/microsoft/winget-cli/releases)); webapp uses this path for Full dev setup.
- **`assets/vbox/`**  VirtualBox: place ISOs and OVA/OVF here; webapp Create VM and Attach ISO list and use these files. See [assets/README.md](assets/README.md) and [assets/vbox/README.md](assets/vbox/README.md) (incl. Win 11 Pro VM asset).

### Configuration (environment)

- **`VIRTUALIZATION_MCP_PORT`**  Port for MCP HTTP/SSE transport when the server is run with HTTP (default: **10702**, in SOTA range 1070010800). Stdio (Claude Desktop) does not use this.
- **`TOOL_MODE`**  `production` (default) or `testing`; see [Tool Mode Configuration](docs/mcp-technical/TOOL_MODE_CONFIGURATION.md).

---

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx virtualization-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "virtualization-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/virtualization-mcp", "run", "virtualization-mcp"]
  }
}
```
### For Claude Desktop (Recommended)

1. **Download MCPB Package:**
   - Go to [Releases](https://github.com/sandraschi/virtualization-mcp/releases/latest)
   - Download `virtualization-mcp-{version}.mcpb`

2. **Install in Claude Desktop:**
   - Open Claude Desktop
   - Go to Settings  Extensions
   - Drag and drop the `.mcpb` file
   - Restart Claude Desktop

3. **Start Managing VMs:**
   ```
   "List all my virtual machines"
   "Create a new Ubuntu VM with 4GB RAM"
   "Take a snapshot of my-vm"
   ```

### For Python / Development

```bash
# From GitHub release
pip install https://github.com/sandraschi/virtualization-mcp/releases/download/v1.0.1b2/virtualization_mcp-1.0.1b2-py3-none-any.whl

# Or from git
pip install git+https://github.com/sandraschi/virtualization-mcp.git

# Or for development
git clone https://github.com/sandraschi/virtualization-mcp.git
cd virtualization-mcp
uv sync --dev
```

### Prerequisites

- **VirtualBox 7.0+** installed and in PATH
- **Python 3.10+** (for manual installation)
- **Claude Desktop** (for MCPB installation)

---

##  Features

### VM Lifecycle Management
- Create VMs from templates or custom configurations
- Start, stop, pause, resume, reset VMs
- Clone VMs (full or linked clones)
- Delete VMs with optional disk cleanup
- Get detailed VM information and metrics

### Storage Management
- Create virtual disks (VDI, VMDK, VHD formats)
- Attach/detach storage devices
- Manage storage controllers (IDE, SATA, SCSI, NVMe)
- Configure disk properties and settings
- Shared folder management

### Network Configuration
- Configure network adapters (NAT, Bridged, Host-only, Internal)
- Set up port forwarding rules
- Manage host-only networks
- Advanced network adapter configuration

### Snapshot Management
- Create snapshots with descriptions
- List all snapshots for a VM
- Restore VMs to previous snapshots
- Delete individual snapshots
- Snapshot-based cloning

### System Information
- Host system information
- VirtualBox version details
- Available OS types
- VM performance metrics
- Screenshot capture

---

##  Tool Modes

### Production Mode (Default) - 6-7 Tools

Clean, organized interface  for daily use:

1. **vm_management** - Complete VM lifecycle (10 operations)
2. **network_management** - Network configuration (5 operations)
3. **snapshot_management** - Snapshot operations (4 operations)
4. **storage_management** - Storage & disk management (6 operations)
5. **system_management** - System info & diagnostics (5 operations)
6. **discovery_management** - Help & tool info (4 operations)
7. **hyperv_management** - Hyper-V VMs (4 operations, Windows only)

**Total:** 33 operations in 6 tools (7 on Windows)

**Note:** discovery_management is app-specific help (NOT the same as MCP protocol's native tools/list)

### Testing Mode - 60+ Tools

All individual functions plus portmanteau tools for development and debugging.

**Switch modes in `mcp_config.json`:**
```json
{
  "env": {
    "TOOL_MODE": "production"  // or "testing"
  }
}
```

See [Tool Mode Configuration](docs/mcp-technical/TOOL_MODE_CONFIGURATION.md) for details.

---

##  Usage Examples

### Basic VM Management

```
User: "List all my VMs"
Claude: Uses vm_management(action="list")

User: "Create a Ubuntu development VM"
Claude: Uses vm_management(action="create", vm_name="ubuntu-dev", 
        os_type="Ubuntu_64", memory_mb=4096, disk_size_gb=50)

User: "Start the VM ubuntu-dev"
Claude: Uses vm_management(action="start", vm_name="ubuntu-dev")
```

### Snapshot Workflow

```
User: "Create a snapshot of ubuntu-dev called 'clean-state'"
Claude: Uses snapshot_management(action="create", vm_name="ubuntu-dev",
        snapshot_name="clean-state")

User: "List all snapshots for ubuntu-dev"
Claude: Uses snapshot_management(action="list", vm_name="ubuntu-dev")

User: "Restore ubuntu-dev to the clean-state snapshot"
Claude: Uses snapshot_management(action="restore", vm_name="ubuntu-dev",
        snapshot_name="clean-state")
```

### Network Configuration

```
User: "Set up NAT networking on my VM"
Claude: Uses network_management(action="configure_adapter", 
        vm_name="my-vm", adapter_slot=0, network_type="nat")

User: "Create a host-only network called dev-network"
Claude: Uses network_management(action="create_network",
        network_name="dev-network")
```

---

##  Documentation

### Quick Start
- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [Claude Desktop Setup](CLAUDE_DESKTOP_SETUP.md) - Integration guide

### Technical Documentation
- [Tool Mode Configuration](docs/mcp-technical/TOOL_MODE_CONFIGURATION.md) - Switch between modes
- [FastMCP 3.1.0 Compliance](docs/mcp-technical/FASTMCP_2.12_COMPLIANCE.md) - Integration details
- [Docstring Coverage](docs/mcp-technical/DOCSTRING_COVERAGE.md) - 100% coverage report
- [Project Status](docs/mcp-technical/PROJECT_STATUS_FINAL.md) - Complete status

### MCPB Packaging
- [MCPB Building Guide](docs/mcpb-packaging/MCPB_BUILDING_GUIDE.md) - Package creation
- [Implementation Summary](docs/mcpb-packaging/MCPB_IMPLEMENTATION_SUMMARY.md) - Technical details

### User Guides
- [VM Management](docs/concepts/vm_management.md) - VM operations
- [Network Configuration](docs/concepts/network_configuration.md) - Networking
- [Snapshot Management](docs/concepts/snapshot_management.md) - Snapshots
- [Storage Management](docs/concepts/storage_management.md) - Disks & storage

---

##  AI Prompt Templates

8 comprehensive templates included (25+ KB total):

- **backup-strategies.md** - Backup and disaster recovery patterns
- **complete-scenarios.md** - Full deployment scenarios
- **network-configuration.md** - Network setup guides
- **security--practices.md** - Security hardening
- **snapshot-management.md** - Snapshot strategies
- **storage-optimization.md** - Storage configuration
- **vm-deployment-strategies.md** - Deployment patterns (345 lines!)
- **vm-templates.md** - Template usage and customization

---

##  Architecture

### Built With:
- **FastMCP 3.1.0+** - Prompts, skills, Context, progress reporting, optional LLM sampling in tools
- **UV** - Modern Python package manager
- **Ruff** - Fast Python linter & formatter
- **pytest** - Comprehensive test suite
- **VirtualBox 7.0+** - Virtualization platform

### Tool Organization:
- **Portmanteau Tools** - Action-based consolidated operations
- **Individual Tools** - Direct function access (testing mode)
- **Service Layer** - Business logic and validation
- **VBox Adapter** - VirtualBox integration
- **Plugin System** - Extensible architecture

---

##  Testing

### Run Tests:
From a **clone** of this repo at the **repository root** (see [Development Setup](#development-setup) below if you have not cloned yet):

```bash
# Install development dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=virtualization_mcp --cov-report=term-missing
```

### Test Statistics:
- **Total Tests:** 605
- **Passing:** 499 (82.5%)
- **Coverage:** 39%  Target: 80% (GLAMA Gold Standard)
- **Integration Tests:** VBox-aware (mocked when unavailable)

---

##  Configuration

### Basic Setup (Claude Desktop):

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/virtualization-mcp",
        "run",
        "virtualization-mcp"
      ],
      "env": {
        "TOOL_MODE": "production",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Advanced Configuration:

See `.env.example` for all available settings:
- Tool mode selection
- VirtualBox path configuration
- Logging levels
- Timeouts and limits
- Default VM settings
- Feature flags

---

##  Contributing

We welcome contributions! Please see:
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Security Policy](SECURITY.md) - Security considerations
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

### Development Setup:

```bash
# Clone repository
git clone https://github.com/sandraschi/virtualization-mcp.git
cd virtualization-mcp

# Install with UV
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

---

##  Project Status

-  **Production Ready** - v1.0.1b2 released
-  **Quality** - 0 linting errors, 499 tests passing
-  **Documentation** - 100% docstring coverage
-  **MCPB Packaged** - Optimized for Claude Desktop
-  **FastMCP Compliant** - Version 2.12.4
-  **Clean Repository** - Professional organization

See [Project Status](docs/mcp-technical/PROJECT_STATUS_FINAL.md) for complete details.

---

##  Roadmap & Extensions

### **Coming Soon**
- **VM Templates**: Pre-built configurations for Ubuntu, Windows, macOS
- **Advanced Monitoring**: Real-time performance metrics and health checks
- **Security Features**: Vulnerability scanning and access control
- **Enhanced Networking**: Visual topology mapping and advanced port management

### **Planned Features**
- **Plugin System**: Extensible architecture for custom functionality
- **Cloud Integration**: AWS/Azure VM synchronization
- **CI/CD Support**: Jenkins/GitHub Actions integration
- **Interactive CLI**: Direct command-line interface

### **Quick Wins**
-  Progress tracking for long operations
-  Health check endpoints
-  Configuration validation tools
-  Operation history and audit logging

*See [Extensions & Improvements Guide](docs/planning/EXTENSIONS_AND_IMPROVEMENTS.md) for detailed roadmap.*

---

##  Links

- **Repository:** https://github.com/sandraschi/virtualization-mcp
- **Releases:** https://github.com/sandraschi/virtualization-mcp/releases
- **Issues:** https://github.com/sandraschi/virtualization-mcp/issues
- **Latest Release:** [v1.0.1b2](https://github.com/sandraschi/virtualization-mcp/releases/tag/v1.0.1b2)

---

##  Contact

**Author:** Sandra Schi  
**Email:** sandraschipal@protonmail.com  
**GitHub:** [@sandraschi](https://github.com/sandraschi)

---


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Quick Start

1. Download `.mcpb` from releases
2. Drop into Claude Desktop
3. Ask: **"What can you do with VirtualBox?"**
4. Start managing VMs with natural language!

**Manage VirtualBox VMs effortlessly through Claude Desktop!** 


##  Webapp Dashboard

This MCP server includes a free, premium web interface for monitoring and control.
By default, the web dashboard runs on port **10700**.
*(Assigned ports: **10700** (Web dashboard))*

To start the webapp:
1. Navigate to the `webapp` (or `web`, `frontend`) directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10700` in your browser.
