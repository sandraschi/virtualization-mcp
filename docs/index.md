# VBoxMCP Documentation

Welcome to the VBoxMCP documentation! VBoxMCP is a FastMCP 2.12+ compliant server that provides comprehensive management of VirtualBox virtual machines through a standardized MCP interface.

## Quick Start

1. **Install VBoxMCP**:
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

## Features

- **Complete VM Lifecycle Management**: Create, start, stop, pause, resume, reset, and delete VMs
- **Advanced Storage Management**: Handle disks, ISOs, and storage controllers
- **Snapshot Management**: Take, restore, delete, and manage VM snapshots
- **Network Configuration**: Set up NAT, Bridged, Host-Only, and Internal networks
- **Resource Allocation**: Configure CPU, memory, and storage resources
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Claude Desktop Ready**: Tested and verified integration

## Available Tools

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

### Snapshot Management
- `list_snapshots`: List snapshots for a VM
- `create_snapshot`: Create a snapshot of a VM
- `restore_snapshot`: Restore a VM to a snapshot
- `delete_snapshot`: Delete a snapshot

### Storage Management
- `list_storage_controllers`: List storage controllers for a VM
- `create_storage_controller`: Create a storage controller for a VM
- `remove_storage_controller`: Remove a storage controller from a VM

### Network Management
- `list_hostonly_networks`: List all host-only networks
- `create_hostonly_network`: Create a host-only network
- `remove_hostonly_network`: Remove a host-only network

### System Information
- `get_system_info`: Get system information
- `get_vbox_version`: Get VirtualBox version information
- `list_ostypes`: List available OS types

## Requirements

- Python 3.8 or higher
- VirtualBox 7.0 or higher (with Extension Pack recommended)
- FastMCP 2.12.2+

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/sandraschi/virtualization-mcp/issues)
- **Documentation**: [Complete documentation](https://virtualization-mcp.readthedocs.io/)
- **Discussions**: [Community discussions](https://github.com/sandraschi/virtualization-mcp/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.