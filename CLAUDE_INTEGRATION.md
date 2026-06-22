# Claude Desktop Integration Guide

This document provides comprehensive instructions for integrating the virtualization-mcp server with Claude Desktop, including setup, configuration, and troubleshooting.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Tool Reference](#tool-reference)
- [Development](#development)

## Prerequisites

- Python 3.8 or higher
- VirtualBox 6.1 or higher
- Claude Desktop installed and configured
- Administrative privileges (for VirtualBox operations)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/yourusername/virtualization-mcp.git
   cd virtualization-mcp
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt  # For development
   ```

## Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file (typically `~/.config/claude/config.json` on Linux/macOS or `%APPDATA%\claude\config.json` on Windows):

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "python",
      "args": ["-m", "virtualization-mcp.server_enhanced", "--debug"],
      "timeout": 30,
      "autoStart": true,
      "environment": {
        "PATH": "${PATH}",
        "VBOX_INSTALL_PATH": "C:\\Program Files\\Oracle\\VirtualBox"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VBOX_INSTALL_PATH` | Path to VirtualBox installation | Auto-detected |
| `VBOX_USER_HOME` | Path to VirtualBox configuration | `~/.VirtualBox` |
| `VBOX_LOG_LEVEL` | Logging level (error, warn, info, debug) | `info` |

## Testing

### Running Integration Tests

```bash
# Run all tests
python test_claude_integration.py

# Run with debug output
python test_claude_integration.py --debug
```

### Manual Testing

1. Start the virtualization-mcp server manually:
   ```bash
   python -m virtualization-mcp.server_enhanced --debug
   ```

2. In Claude Desktop, try listing VMs:
   ```
   /virtualization-mcp list_vms
   ```

## Tool Reference

### Core VM Management

#### `create_vm`
Create a new virtual machine from a template.

**Parameters:**
- `name` (str): Unique name for the VM
- `template` (str): Template name (e.g., 'ubuntu-dev', 'windows-test')
- `memory_mb` (int, optional): Memory in MB (overrides template default)
- `disk_gb` (int, optional): Disk size in GB (overrides template default)

**Example:**
```
/virtualization-mcp create_vm name="my-vm" template="ubuntu-dev" memory_mb=4096 disk_gb=50
```

#### `start_vm`
Start a virtual machine.

**Parameters:**
- `name` (str): Name of the VM to start
- `headless` (bool): Start in headless mode (no GUI)

**Example:**
```
/virtualization-mcp start_vm name="my-vm" headless=true
```

#### `stop_vm`
Stop a running virtual machine.

**Parameters:**
- `name` (str): Name of the VM to stop
- `force` (bool): Force stop if graceful shutdown fails

**Example:**
```
/virtualization-mcp stop_vm name="my-vm" force=false
```

#### `delete_vm`
Delete a virtual machine.

**Parameters:**
- `name` (str): Name of the VM to delete
- `delete_disk` (bool): Also delete associated disk images

**Example:**
```
/virtualization-mcp delete_vm name="my-vm" delete_disk=true
```

#### `list_vms`
List all virtual machines.

**Parameters:**
- `state` (str, optional): Filter by state ('running', 'poweroff', 'saved', 'all')

**Example:**
```
/virtualization-mcp list_vms state="running"
```

### Snapshot Management

#### `create_snapshot`
Create a snapshot of a virtual machine.

**Parameters:**
- `vm_name` (str): Name of the VM
- `snapshot_name` (str): Name for the snapshot
- `description` (str, optional): Description of the snapshot

**Example:**
```
/virtualization-mcp create_snapshot vm_name="my-vm" snapshot_name="before-update" description="Before applying updates"
```

#### `restore_snapshot`
Restore a virtual machine to a previous snapshot.

**Parameters:**
- `vm_name` (str): Name of the VM
- `snapshot_name` (str): Name of the snapshot to restore

**Example:**
```
/virtualization-mcp restore_snapshot vm_name="my-vm" snapshot_name="before-update"
```

#### `list_snapshots`
List snapshots for a virtual machine.

**Parameters:**
- `vm_name` (str): Name of the VM

**Example:**
```
/virtualization-mcp list_snapshots vm_name="my-vm"
```

### Network Management

#### `configure_port_forwarding`
Configure port forwarding for a VM.

**Parameters:**
- `vm_name` (str): Name of the VM
- `rule_name` (str): Name for the port forwarding rule
- `protocol` (str): 'tcp' or 'udp'
- `host_port` (int): Port on the host
- `guest_port` (int): Port on the guest
- `guest_ip` (str, optional): IP address of the guest (default: '')
- `host_ip` (str, optional): IP address on the host (default: '127.0.0.1')

**Example:**
```
/virtualization-mcp configure_port_forwarding vm_name="my-vm" rule_name="ssh" protocol="tcp" host_port=2222 guest_port=22
```

## Troubleshooting

### Common Issues

#### 1. VirtualBox Not Found
**Error:** `VBoxManage not found in PATH`
**Solution:** Ensure VirtualBox is installed and the installation directory is in your PATH, or set the `VBOX_INSTALL_PATH` environment variable.

#### 2. Permission Denied
**Error:** `Permission denied` when accessing VirtualBox
**Solution:** Make sure your user has the necessary permissions to access VirtualBox. On Linux, you may need to add your user to the `vboxusers` group.

#### 3. VM Creation Fails
**Error:** `Failed to create VM: VBOX_E_OBJECT_NOT_FOUND`
**Solution:** Verify that the specified template exists and is properly configured.

### Logging

Logs are written to `virtualization-mcp.log` in the current working directory by default. To increase log verbosity, set the `VBOX_LOG_LEVEL` environment variable to `debug`:

```bash
export VBOX_LOG_LEVEL=debug
python -m virtualization-mcp.server_enhanced
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test
pytest tests/test_vm_operations.py -v
```

### Code Style

This project uses:
- Black for code formatting
- Flake8 for linting
- Mypy for type checking

To format and check the code:

```bash
# Format code
black .

# Run linter
flake8

# Check types
mypy .
```

### Building the Package

```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



