# virtualization-mcp Tools API Reference

Complete reference for all MCP tools provided by virtualization-mcp.

## Portmanteau Tools (Consolidated)

### vm_management
Comprehensive virtual machine management operations.

**Actions:**
- `list` - List all virtual machines
- `create` - Create a new virtual machine
- `start` - Start a virtual machine
- `stop` - Stop a virtual machine
- `delete` - Delete a virtual machine
- `clone` - Clone a virtual machine
- `reset` - Reset a virtual machine
- `pause` - Pause a virtual machine
- `resume` - Resume a paused virtual machine
- `info` - Get detailed VM information

**Parameters:**
- `action` (required): Operation to perform
- `vm_name`: VM name (required for most actions)
- `os_type`: OS type for create action
- `memory_mb`: Memory in MB for create action
- `disk_size_gb`: Disk size for create action
- Additional kwargs passed to underlying tools

**Example:**
```python
# Create a new VM
await vm_management(
    action="create",
    vm_name="MyVM",
    os_type="Ubuntu_64",
    memory_mb=4096,
    disk_size_gb=50
)

# Start VM
await vm_management(action="start", vm_name="MyVM")
```

### network_management
Comprehensive network management operations.

**Actions:**
- `list` - List all networks
- `create` - Create a new network
- `remove` - Remove a network
- `list_adapters` - List VM network adapters
- `configure_adapter` - Configure a VM network adapter

**Parameters:**
- `action` (required): Operation to perform
- `network_name`: Network name
- `vm_name`: VM name for adapter operations
- `adapter_slot`: Adapter number (0-7)
- `network_type`: Network type (nat, bridged, hostonly, internal)

### storage_management
Comprehensive storage management operations.

**Actions:**
- `list` - List storage controllers
- `create_controller` - Create storage controller
- `attach_disk` - Attach disk to controller
- `detach_disk` - Detach disk from controller
- `create_disk` - Create new virtual disk
- `delete_disk` - Delete virtual disk

**Parameters:**
- `action` (required): Operation to perform
- `vm_name` (required): Virtual machine name
- `controller_name`: Storage controller name
- `disk_path`: Path to disk file
- `size_mb`: Disk size in MB

### snapshot_management
Comprehensive snapshot management operations.

**Actions:**
- `list` - List all snapshots for a VM
- `create` - Create a new snapshot
- `restore` - Restore to a snapshot
- `delete` - Delete a snapshot

**Parameters:**
- `action` (required): Operation to perform
- `vm_name` (required): Virtual machine name
- `snapshot_name`: Snapshot name
- `description`: Snapshot description

### system_management
System information and management.

**Actions:**
- `info` - Get system information
- `version` - Get VirtualBox version
- `ostypes` - List available OS types

**Parameters:**
- `action` (required): Operation to perform

## Individual Tools

### VM Tools
- `list_vms()` - List all VMs
- `get_vm_info(vm_name)` - Get VM details
- `create_vm(vm_name, os_type, memory_mb, cpu_count, disk_size_gb)` - Create VM
- `start_vm(vm_name, headless)` - Start VM
- `stop_vm(vm_name, force)` - Stop VM
- `delete_vm(vm_name, delete_disks)` - Delete VM
- `clone_vm(source_vm, clone_name)` - Clone VM
- `reset_vm(vm_name)` - Reset VM
- `pause_vm(vm_name)` - Pause VM
- `resume_vm(vm_name)` - Resume VM

### Snapshot Tools
- `list_snapshots(vm_name)` - List VM snapshots
- `create_snapshot(vm_name, snapshot_name, description)` - Create snapshot
- `restore_snapshot(vm_name, snapshot_name)` - Restore snapshot
- `delete_snapshot(vm_name, snapshot_name)` - Delete snapshot

### Network Tools
- Network configuration and management tools

### Storage Tools
- Storage controller and disk management tools

### System Tools
- `get_system_info()` - Get host system information
- `get_vbox_version()` - Get VirtualBox version
- `list_os_types()` - List supported OS types

### Monitoring Tools
- `get_vm_metrics(vm_name)` - Get VM resource metrics
- VM performance monitoring

### Security Tools
- Security scanning and malware analysis

### Backup Tools
- VM backup and restore operations

### Development Tools
- Sandbox management
- API documentation generation

## Error Handling

All tools return consistent error responses:

```python
{
    "success": False,
    "error": "Error message",
    "details": "Additional error details"
}
```

## Rate Limiting

Tools implement rate limiting to prevent system overload:
- Default: 100 requests per minute
- Configurable via settings

## Best Practices

1. **Always check VM state** before operations
2. **Use snapshots** before risky operations
3. **Monitor resource usage** regularly
4. **Implement error handling** in your code
5. **Use portmanteau tools** for simpler API

## See Also

- [User Guide](../user-guides/USER_GUIDE.md)
- [Configuration](../user-guides/Configuration.md)
- [Examples](../examples/)
- [Troubleshooting](../user-guides/Troubleshooting.md)

