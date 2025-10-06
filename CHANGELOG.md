# Changelog

All notable changes to the VirtualBox MCP Server will be documented in this file.

## [0.1.0b1] - 2025-08-11

### 🎉 Beta Release

This is the first beta release of VirtualBox MCP Server, providing core VirtualBox management through the MCP protocol. This beta release focuses on core functionality and stability for early adopters.

### 🚀 New Features

#### Core Functionality
- **MCP Protocol Support**: Basic implementation of the MCP protocol with STDIO support
- **VM Lifecycle**: Start, stop, pause, resume, and delete VMs
- **Basic VM Management**: Create and configure VMs with basic settings
- **Network Configuration**: Support for basic networking modes (NAT, Bridged)

### 🛠️ Improvements
- Initial implementation of core VM management features
- Basic error handling and logging
- Documentation for getting started

### 🐛 Bug Fixes
- Fixed issues with VM state management
- Resolved path handling issues on Windows
- Improved error messages for common configuration issues

## [1.0.0] - 2025-08-10

### 🎉 Initial Release

This is the first stable release of VirtualBox MCP Server, providing comprehensive VirtualBox management through the MCP protocol. This release focuses on stability, performance, and ease of integration with MCP clients like Claude Desktop.

### 🚀 New Features

#### Core Functionality

- **Full FastMCP 2.10+ Compliance**: Complete implementation of the MCP protocol with STDIO support
- **Comprehensive VM Management**: Create, start, stop, pause, resume, delete, and clone VMs
- **Template System**: Predefined templates for common OS configurations (Windows, Linux, macOS)
- **Snapshot Management**: Create, restore, and manage VM snapshots
- **Resource Configuration**: Fine-grained control over CPU, memory, and storage allocation
- **Network Configuration**: Support for NAT, Bridged, and Host-Only networking modes
- **Storage Management**: Virtual disk creation, attachment, and management
- **ISO Management**: Mount and boot from ISO images
- **Shared Folders**: Easy file sharing between host and guest systems
- **Clipboard & Drag'n'Drop**: Seamless integration with host system

#### MCP Tools

##### VM Management

- `list_vms`: List all available VMs with their states
- `get_vm_info`: Get detailed information about a VM
- `create_vm`: Create a new VM from template
- `register_vm`: Register an existing VM
- `unregister_vm`: Unregister a VM without deleting files
- `start_vm`: Start a virtual machine
- `stop_vm`: Stop a virtual machine gracefully
- `reset_vm`: Forcefully reset a virtual machine
- `pause_vm`: Pause a running VM
- `resume_vm`: Resume a paused VM
- `delete_vm`: Delete a VM and all associated files

##### Snapshot Management

- `create_snapshot`: Create a VM snapshot
- `restore_snapshot`: Restore VM to a previous state
- `delete_snapshot`: Remove a snapshot
- `list_snapshots`: List all snapshots for a VM
- `get_snapshot_info`: Get information about a specific snapshot

##### Storage & Media

- `list_hdds`: List available virtual hard disks
- `create_hdd`: Create a new virtual hard disk
- `clone_hdd`: Clone an existing virtual disk
- `list_dvds`: List available virtual optical drives
- `mount_iso`: Mount an ISO file to a virtual drive
- `unmount_iso`: Unmount an ISO from a virtual drive
- `list_media`: List all known media (HDDs, ISOs, etc.)

##### Network Configuration

- `list_network_adapters`: List network adapters for a VM
- `modify_network_adapter`: Change network adapter settings
- `create_nat_network`: Create a new NAT network
- `list_nat_networks`: List all NAT networks
- `remove_nat_network`: Remove a NAT network

##### System & Resources

- `modify_vm`: Modify VM settings (CPU, memory, etc.)
- `execute_command`: Run commands inside a VM
- `get_guest_properties`: Read guest OS properties
- `set_guest_properties`: Set guest OS properties
- `get_guest_info`: Get guest OS information

##### Shared Folders

- `add_shared_folder`: Add a shared folder to a VM
- `remove_shared_folder`: Remove a shared folder
- `list_shared_folders`: List all shared folders for a VM

#### Security Features

- **Sandboxed Operations**: All VM operations run in isolated environments
- **Input Validation**: Comprehensive validation of all inputs to prevent injection attacks
- **Secure Process Execution**: Safe execution of VirtualBox commands with proper argument escaping
- **VM Isolation**: Strong isolation between VMs and host system
- **Network Security**: Configurable network security policies and firewall rules
- **Access Control**: Role-based access control for VM operations
- **Secure Credential Storage**: Safe handling of authentication credentials
- **Audit Logging**: Comprehensive logging of all operations for security auditing

#### Documentation

- **API Documentation**: Complete reference for all MCP tools and endpoints
- **Getting Started Guide**: Quick start tutorial for new users
- **Templates Reference**: Documentation for all included VM templates
- **Troubleshooting**: Common issues and solutions
- **Security Guide**: Best practices for secure configuration
- **Performance Tuning**: Tips for optimizing VM performance
- **Development Guide**: For contributors and plugin developers
- **API Examples**: Code samples for common use cases
- **FAQ**: Answers to frequently asked questions

### 🔧 Changes

- **Architecture**
  - Modular plugin system
  - Improved error handling with detailed error messages
  - Enhanced performance for VM operations
  - Asynchronous I/O operations
  - Better resource management
  - Improved logging system

- **Configuration**
  - Simplified MCP configuration
  - Environment variable support
  - Better handling of VirtualBox paths
  - Automatic detection of VirtualBox installation

### 🐛 Bug Fixes

- Fixed issues with VM state detection
- Resolved memory leaks in long-running operations
- Fixed network configuration issues
- Improved error handling for missing dependencies
- Fixed issues with special characters in VM names
- Resolved path handling issues on Windows
- Fixed race conditions in concurrent operations

### 📦 Installation

#### Prerequisites

- Python 3.8 or higher
- VirtualBox 7.0 or higher
- VirtualBox Extension Pack (recommended)

#### Option 1: From PyPI (Recommended)

```bash
pip install vboxmcp
```

#### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/sandraschi/vboxmcp.git
cd vboxmcp

# Install in development mode
pip install -e .
```

#### Option 3: DXT Package (For Claude Desktop)

1. Download the latest `vboxmcp.dxt` package from the [releases page](https://github.com/sandraschi/vboxmcp/releases)
2. Drag and drop the file into your Claude Desktop window

### 🚀 Quick Start

1. Start the MCP server:

   ```bash
   python -m vboxmcp.minimal_server
   ```

2. In Claude Desktop, use MCP tools like:

   ```python
   list_vms()
   create_vm(name="my-vm", template="ubuntu-2204")
   start_vm(name="my-vm")
   ```

### 📚 Documentation

For detailed documentation, please visit our [GitHub Wiki](https://github.com/sandraschi/vboxmcp/wiki).

### 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Previous Versions

<details>
<summary>Click to view previous versions</summary>

### [0.9.0] - 2025-07-20
- Initial beta release
- Basic VM management functionality
- MCP tool registration
- Core architecture implementation

</details>

```bash
dxt install vboxmcp.dxt
```

#### Prerequisites

- Claude Desktop installed
- VirtualBox (for VM management features)
- Python 3.8+ (included with Claude Desktop)

### 📚 Documentation
Full documentation is available in the [GitHub Wiki](https://github.com/sandraschi/vboxmcp/wiki)

## [0.9.0] - 2025-07-15

### Added
- Initial beta release
- Basic VM management
- Snapshot support
- Network configuration
