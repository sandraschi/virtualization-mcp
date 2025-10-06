# VirtualBox MCP Server

**v1.0.0 - FastMCP 2.12+ compliant VirtualBox management server with full MCP client support**

> **✅ Production Ready**: virtualization-mcp is now fully functional and ready for production use with Claude Desktop and other MCP clients!

[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.2-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)
[![VirtualBox](https://img.shields.io/badge/VirtualBox-7.0+-orange)](https://virtualbox.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI/CD](https://github.com/sandraschi/virtualization-mcp/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/sandraschi/virtualization-mcp/actions)
[![PyPI](https://img.shields.io/pypi/v/virtualization-mcp)](https://pypi.org/project/virtualization-mcp/)
[![Documentation Status](https://readthedocs.org/projects/virtualization-mcp/badge/?version=latest)](https://virtualization-mcp.readthedocs.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

## 🚀 Overview

VirtualBox MCP Server (virtualization-mcp) is a FastMCP 2.12+ compliant server that provides comprehensive management of VirtualBox virtual machines through a standardized MCP interface. This production-ready release offers complete VM lifecycle management, advanced features, and seamless integration with Claude Desktop.

### ✨ Key Features

- **Complete VM Lifecycle Management**: Create, start, stop, pause, resume, reset, and delete VMs with simple commands
- **Advanced Storage Management**: Handle disks, ISOs, and storage controllers with ease
- **Snapshot Management**: Take, restore, delete, and manage VM snapshots for testing workflows
- **Network Configuration**: Set up NAT, Bridged, Host-Only, and Internal networks
- **Resource Allocation**: Configure CPU, memory, and storage resources
- **Cross-Platform**: Works on Windows, Linux, and macOS (with VirtualBox 7.0+ support)
- **Secure**: Sandboxed operations with proper access controls
- **Extensible**: Plugin architecture for custom functionality
- **MCP 2.12+ Compatible**: Full support for MCP tool discovery and invocation
- **Comprehensive API**: Programmatic access to all VirtualBox features
- **Claude Desktop Ready**: Tested and verified to work with Claude Desktop
- **Production Ready**: Stable, reliable, and ready for daily use

## 🆕 Latest Updates (v1.0.0)

### ✅ Server Startup Fixed
- **Resolved Import Issues**: Fixed relative import problems that prevented server startup
- **FastMCP Compatibility**: Updated to work with FastMCP 2.12.2+ API
- **AsyncIO Management**: Fixed event loop conflicts for proper server operation
- **Tool Registration**: Simplified and optimized tool registration system
- **Claude Desktop Integration**: Verified working integration with Claude Desktop

### 🔧 Technical Improvements
- **Simplified Tool API**: Removed deprecated parameters and streamlined tool definitions
- **Better Error Handling**: Comprehensive error handling with clear messages
- **Plugin System**: Enhanced plugin architecture with Hyper-V and Windows Sandbox support
- **Configuration Management**: Improved configuration system with environment variables
- **Logging System**: Enhanced logging with proper levels and formatting

## 📚 Documentation

For detailed documentation, please visit our [documentation site](https://virtualization-mcp.readthedocs.io/).

### 📖 Quick Start

### 🛠️ Using with Claude Desktop

1. **Install virtualization-mcp**:
   ```bash
   pip install virtualization-mcp
   ```

2. **Configure Claude Desktop**:
   Add the following to your Claude Desktop MCP configuration:
   ```json
   {
     "mcpServers": {
       "virtualization-mcp": {
         "command": "python",
         "args": ["-m", "virtualization-mcp"],
         "env": {
           "PYTHONPATH": "src",
           "VBOX_INSTALL_PATH": "C:\\Program Files\\Oracle\\VirtualBox",
           "VBOX_USER_HOME": "%USERPROFILE%\\VirtualBox VMs",
           "DEBUG": "true"
         }
       }
     }
   }
   ```

3. **Start Managing VMs**:
   Use natural language commands in Claude Desktop:
   ```
   "List all my virtual machines"
   "Create a new Ubuntu VM with 4GB RAM and 2 CPUs"
   "Start the VM named 'ubuntu-dev'"
   "Take a snapshot of 'ubuntu-dev' called 'clean-install'"
   ```

### 🛠️ Using FastMCP Inspector (Development)

1. Install FastMCP if you haven't already:
   ```bash
   pip install fastmcp
   ```

2. Start the inspector with your MCP server:
   ```bash
   # From the project root
   fastmcp dev src/virtualization-mcp/all_tools_server.py
   ```

3. Open the web interface at http://127.0.0.1:6274 to test and debug your MCP tools

4. For detailed documentation, see the [FastMCP Inspector Guide](docs/fastmcp_inspector.md)

### Quick Links
- [Getting Started](docs/getting_started.md) - Set up and run your first VM
- [Command Reference](docs/command_reference.md) - Complete list of available commands
- [FastMCP Inspector Guide](docs/fastmcp_inspector.md) - Interactive tool testing and debugging
- [Examples](docs/examples/) - Practical examples and use cases
- [API Reference](docs/api/) - Detailed API documentation
- [Development Guide](docs/development/contributing.md) - Contribute to the project

## 🛠️ Features in Detail

### Virtual Machine Management
- Create, clone, and delete VMs
- Start, stop, pause, and resume VMs
- Configure VM settings (CPU, memory, firmware, etc.)
- Manage VM groups and folders

### Storage Management
- Create and manage virtual disks (VDI, VMDK, VHD, RAW)
- Attach/detach disks to/from VMs
- Mount/unmount ISO images
- Manage storage controllers (SATA, SCSI, IDE, SAS)
- Resize and clone disks
- Snapshot disk states

### Network Management
- Configure network adapters (NAT, NAT Network, Bridged, Host-Only, Internal)
- Set up port forwarding
- Configure network bandwidth limits
- Manage DHCP servers

### Advanced Features
- Manage VM snapshots (create, restore, delete, list)
- Configure shared folders
- Set up shared clipboard and drag-and-drop
- Configure audio and video settings
- Manage USB devices

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- VirtualBox 7.0 or higher (with Extension Pack recommended)
- VirtualBox Python SDK (will be installed automatically)
- Git (for source installation)

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
pip install virtualization-mcp
```

#### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/sandraschi/virtualization-mcp.git
cd virtualization-mcp

# Install in development mode with all dependencies
pip install -e .[dev]
```

### Basic Usage

1. **Start the MCP server**:
   ```bash
   python -m virtualization-mcp
   ```

2. **Use with Claude Desktop**:
   - Add the MCP configuration to Claude Desktop
   - Start managing your VMs with natural language commands

3. **Example commands**:
   ```
   "List all my virtual machines"
   "Create a new Ubuntu VM with 4GB RAM and 2 CPUs"
   "Start the VM named 'ubuntu-dev'"
   "Take a snapshot of 'ubuntu-dev' called 'clean-install'"
   ```

### Server Status

✅ **Server Status**: Fully operational and ready for production use
- All tools registered successfully
- Plugins initialized (Hyper-V Manager, Windows Sandbox Helper)
- FastMCP 2.12.2+ compatibility verified
- Claude Desktop integration tested and working

## 📖 Documentation

### Getting Started
- [Installation Guide](docs/getting_started/installation.md)
- [Configuration](docs/getting_started/configuration.md)
- [First VM](docs/getting_started/first_vm.md)

### Core Concepts
- [Virtual Machines](docs/concepts/virtual_machines.md)
- [Storage](docs/concepts/storage.md)
- [Networking](docs/concepts/networking.md)
- [Snapshots](docs/concepts/snapshots.md)

### Advanced Topics
- [Plugins](docs/advanced/plugins.md)
- [API Reference](docs/api/)
- [Security](docs/advanced/security.md)
- [Performance Tuning](docs/advanced/performance.md)

### Examples
- [Common Workflows](docs/examples/workflows/)
- [Sample Configurations](docs/examples/configs/)
- [Troubleshooting](docs/examples/troubleshooting.md)

## 🛠️ Available Tools

### VM Management
- `list_vms`: List all available VirtualBox VMs
- `get_vm_info`: Get detailed information about a VM
- `start_vm`: Start a virtual machine
- `stop_vm`: Stop a running virtual machine
- `create_vm`: Create a new virtual machine
- `delete_vm`: Delete a virtual machine
- `clone_vm`: Clone a virtual machine
- `reset_vm`: Reset a virtual machine
- `pause_vm`: Pause a virtual machine
- `resume_vm`: Resume a paused virtual machine

### Storage Management
- `list_storage_controllers`: List storage controllers for a VM
- `create_storage_controller`: Create a storage controller for a VM
- `remove_storage_controller`: Remove a storage controller from a VM

### Network Management
- `list_hostonly_networks`: List all host-only networks
- `create_hostonly_network`: Create a host-only network
- `remove_hostonly_network`: Remove a host-only network

### Snapshot Management
- `list_snapshots`: List snapshots for a VM
- `create_snapshot`: Create a snapshot of a VM
- `restore_snapshot`: Restore a VM to a snapshot
- `delete_snapshot`: Delete a snapshot

### System Information
- `get_system_info`: Get system information
- `get_vbox_version`: Get VirtualBox version information
- `list_ostypes`: List available OS types

### Example Tools
- `example_greet`: A simple example tool that greets someone
- `get_counter`: Get the current counter value
- `analyze_file`: Analyze a file for potential malware

### Backup Tools
- `create_vm_backup`: Create a backup of a virtual machine
- `list_vm_backups`: List all VM backups
- `delete_vm_backup`: Delete a VM backup

### Monitoring Tools
- `record_api_request`: Record an API request for metrics
- `record_error`: Record an error for metrics
- `update_vm_metrics`: Update VM-specific metrics
- `update_system_metrics`: Update system-wide metrics

### Security Tools
- `run_security_scan`: Run a security scan on the specified target
- `get_security_test_status`: Get the status of a security test

### Malware Analysis Tools
- `get_analysis`: Get the results of a malware analysis
- `list_analyses`: List all malware analyses with optional filtering
- `delete_analysis`: Delete a malware analysis and associated files
- `list_quarantine`: List all files in quarantine

## 🔧 Troubleshooting

### Common Issues

**Server won't start**
```
Error: ImportError: attempted relative import with no known parent package
Solution: Ensure PYTHONPATH is set to 'src' in your MCP configuration
```

**VBoxManage not found**
```
Error: VBoxManage command not found
Solution: Add VirtualBox to PATH or set VBOX_INSTALL_PATH environment variable
```

**FastMCP compatibility issues**
```
Error: FastMCP.tool() got an unexpected keyword argument
Solution: Update to FastMCP 2.12.2+ and ensure proper tool registration
```

**Claude Desktop connection issues**
```
Error: Server not responding
Solution: Check MCP configuration JSON and ensure server is running
```

### Getting Help

- **GitHub Issues**: [Report bugs and request features](https://github.com/sandraschi/virtualization-mcp/issues)
- **Documentation**: [Complete documentation](https://virtualization-mcp.readthedocs.io/)
- **Discussions**: [Community discussions](https://github.com/sandraschi/virtualization-mcp/discussions)

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to contribute to this project.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - For the MCP server framework
- [VirtualBox](https://www.virtualbox.org/) - For the powerful virtualization platform
- [Python](https://www.python.org/) - For being awesome

## 📬 Contact

For questions and support, please open an issue on our [GitHub repository](https://github.com/sandraschi/virtualization-mcp/issues).

## 📊 Project Status

✅ **Production Ready**: virtualization-mcp v1.0.0 is fully functional and ready for production use
- ✅ Server startup issues resolved
- ✅ FastMCP 2.12.2+ compatibility verified
- ✅ Claude Desktop integration working
- ✅ All core tools operational
- ✅ Plugin system functional

![GitHub last commit](https://img.shields.io/github/last-commit/sandraschi/virtualization-mcp)
![GitHub issues](https://img.shields.io/github/issues-raw/sandraschi/virtualization-mcp)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/sandraschi/virtualization-mcp)

## 🔗 Related Projects

- [FastMCP](https://github.com/jlowin/fastmcp) - The MCP server framework
- [VirtualBox](https://www.virtualbox.org/) - The virtualization platform
- [Claude Desktop](https://www.anthropic.com/product) - MCP client for natural language interaction

---

**Built with Austrian efficiency for practical VirtualBox automation through Claude Desktop.** 🚀

*Ready for production deployment in minutes, not hours.*



