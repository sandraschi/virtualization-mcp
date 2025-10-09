# virtualization-mcp Examples

Practical examples demonstrating common workflows and use cases.

## Basic Examples

### Create and Start a VM

```python
from virtualization_mcp import VBoxManager

# Initialize manager
manager = VBoxManager()

# Create a new VM
result = manager.create_vm(
    name="UbuntuDev",
    ostype="Ubuntu_64",
    memory=4096,
    cpus=4
)

# Start the VM
manager.start_vm("UbuntuDev", headless=True)
```

### Using Portmanteau Tools

```python
# Using the vm_management portmanteau tool
# (Recommended for simpler API)

# Create and start VM in one workflow
await vm_management(
    action="create",
    vm_name="DevBox",
    os_type="Ubuntu_64",
    memory_mb=4096,
    disk_size_gb=50
)

await vm_management(action="start", vm_name="DevBox")

# Get VM info
info = await vm_management(action="info", vm_name="DevBox")

# Stop and delete when done
await vm_management(action="stop", vm_name="DevBox")
await vm_management(action="delete", vm_name="DevBox")
```

### Snapshot Management

```python
# Create a snapshot before risky operations
await snapshot_management(
    action="create",
    vm_name="ProductionVM",
    snapshot_name="before-upgrade",
    description="Snapshot before system upgrade"
)

# If something goes wrong, restore
await snapshot_management(
    action="restore",
    vm_name="ProductionVM",
    snapshot_name="before-upgrade"
)
```

### Network Configuration

```python
# Configure VM network adapter
await network_management(
    action="configure_adapter",
    vm_name="WebServer",
    adapter_slot=0,
    network_type="bridged"
)

# List all networks
networks = await network_management(action="list")
```

## Advanced Examples

See the [workflows](workflows/) directory for complex multi-step examples:

- [Backup & Recovery Workflow](workflows/backup_recovery.md)
- [Development Environment Setup](workflows/development_environment.md)

## Configuration Examples

See the [configs](configs/) directory for sample configuration files.

## Claude Desktop Integration

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "python",
      "args": ["-m", "virtualization_mcp"]
    }
  }
}
```

## More Examples

- Check `tests/` directory for comprehensive test examples
- See [User Guide](../user-guides/USER_GUIDE.md) for detailed usage
- Review [API Reference](../api/TOOLS_REFERENCE.md) for all available tools

