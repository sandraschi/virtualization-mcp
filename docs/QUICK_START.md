# Quick Start Guide - virtualization-mcp

Get started with virtualization-mcp in under 5 minutes!

---

## 📦 Installation

### Option 1: Claude Desktop (Recommended)

1. **Download MCPB Package:**
   - Go to [Releases](https://github.com/sandraschi/virtualization-mcp/releases/latest)
   - Download `virtualization-mcp-{version}.mcpb`

2. **Install in Claude Desktop:**
   - Open Claude Desktop
   - Go to Settings → Extensions
   - Drag and drop the `.mcpb` file
   - Restart Claude Desktop

3. **Verify Installation:**
   - Chat with Claude: "List available VirtualBox VMs"
   - Claude should use the virtualization-mcp tools

### Option 2: Python Package

```bash
# From GitHub release (recommended)
pip install https://github.com/sandraschi/virtualization-mcp/releases/download/v1.0.1b2/virtualization_mcp-1.0.1b2-py3-none-any.whl

# Or from git
pip install git+https://github.com/sandraschi/virtualization-mcp.git
```

### Option 3: Development Install

```bash
# Clone repository
git clone https://github.com/sandraschi/virtualization-mcp.git
cd virtualization-mcp

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

---

## 🚀 First Steps

### 1. Verify VirtualBox Installation

```bash
# Check VBoxManage is available
VBoxManage --version
```

### 2. List Your VMs

Ask Claude:
```
Show me all my VirtualBox virtual machines
```

### 3. Create a Test VM

```
Create a new Ubuntu VM called "test-vm" with 2GB RAM and 2 CPUs
```

### 4. Manage VM Lifecycle

```
Start the VM "test-vm"
Check the status of "test-vm"
Stop the VM "test-vm"
```

---

## 🎯 Common Use Cases

### Development Environment Setup

```
Create a development VM named "dev-env" with:
- Ubuntu 22.04
- 4GB RAM
- 4 CPUs
- 50GB disk
```

### Snapshot Management

```
Create a snapshot of "dev-env" named "before-update"
List all snapshots for "dev-env"
Restore "dev-env" to snapshot "before-update"
```

### Network Configuration

```
Show network adapters for "dev-env"
Add NAT network to "dev-env"
Configure port forwarding on "dev-env": host 8080 to guest 80
```

### Template Management

```
Create a Windows 10 Pro VM from template
List all available templates
```

---

## 📚 Available Commands

### VM Lifecycle
- List VMs
- Create VM
- Start/Stop/Pause/Resume VM
- Delete VM
- Clone VM

### VM Information
- Get VM details
- Check VM status
- Show VM properties
- Get resource usage

### Snapshot Management
- Create snapshot
- List snapshots
- Restore snapshot
- Delete snapshot

### Network Management
- Configure adapters
- Set up port forwarding
- Manage NAT networks
- Configure bridged networking

### Storage Management
- Attach/detach disks
- Manage shared folders
- Configure storage controllers

### Advanced Features
- Template management
- Batch operations
- Security configuration
- Performance tuning

---

## 🔧 Configuration

### MCP Server Configuration

If running standalone (not in Claude Desktop):

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
      ]
    }
  }
}
```

### VirtualBox Path (Optional)

If VBoxManage is not in PATH:

```python
# Set environment variable
export VBOX_INSTALL_PATH="/usr/local/bin"

# Or configure in code
from virtualization_mcp.config import Settings
settings = Settings(vbox_path="/custom/path/to/VBoxManage")
```

---

## 🐛 Troubleshooting

### "VBoxManage not found"
**Solution:** Install VirtualBox or add it to PATH
```bash
# Windows
set PATH=%PATH%;C:\Program Files\Oracle\VirtualBox

# Linux/Mac
export PATH=$PATH:/usr/local/bin
```

### "Permission denied"
**Solution:** Run with appropriate permissions
```bash
# Linux: Add user to vboxusers group
sudo usermod -aG vboxusers $USER

# Then logout and login again
```

### "VM already exists"
**Solution:** Use unique VM names or delete existing VM first
```
Delete the VM "test-vm" if it exists
```

---

## 📖 Next Steps

- [View Full Documentation](../README.md)
- [Check Examples](../examples/)
- [Browse Prompts](../mcpb/prompts/)
- [Report Issues](https://github.com/sandraschi/virtualization-mcp/issues)

---

## 💡 Tips

1. **Use Descriptive Names:** Name VMs clearly (e.g., "ubuntu-dev-env", "windows-test")
2. **Take Snapshots:** Before major changes, create snapshots
3. **Resource Planning:** Start with conservative RAM/CPU, increase as needed
4. **Network Testing:** Use NAT for internet, bridged for LAN access
5. **Template Usage:** Create templates for common configurations

---

## 🎉 You're Ready!

Start managing your VirtualBox VMs with natural language through Claude Desktop or your MCP-enabled application!

**Need help?** Ask Claude: "What can you do with VirtualBox?"

