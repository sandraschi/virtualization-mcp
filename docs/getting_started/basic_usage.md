# Basic Usage Guide

## Starting the MCP Server

### Command Line Interface

```bash
# Start the MCP server
virtualization-mcp serve

# Specify host and port
virtualization-mcp serve --host 0.0.0.0 --port 8000

# Enable debug mode
virtualization-mcp serve --debug
```

### Python API

```python
from virtualization-mcp import VBoxManager

# Initialize the manager
manager = VBoxManager()

# Start the MCP server
manager.start_server(host="0.0.0.0", port=8000, debug=True)
```

## Managing Virtual Machines

### Create a New VM

```python
# Using Python API
vm_config = {
    "name": "ubuntu-vm",
    "os_type": "Ubuntu_64",
    "memory_mb": 4096,
    "cpus": 2,
    "storage_gb": 50
}

vm = manager.create_vm(vm_config)
```

### Start a VM

```python
# Start a VM by name
manager.start_vm("ubuntu-vm")

# Start with GUI
manager.start_vm("ubuntu-vm", gui=True)
```

### Stop a VM

```python
# Graceful shutdown
manager.stop_vm("ubuntu-vm")

# Force stop
manager.stop_vm("ubuntu-vm", force=True)
```

## Working with Snapshots

### Create a Snapshot

```python
manager.create_snapshot("ubuntu-vm", "clean-install")
```

### Restore a Snapshot

```python
manager.restore_snapshot("ubuntu-vm", "clean-install")
```

## Storage Management

### Attach a Disk

```python
# Attach an existing disk
manager.attach_disk("ubuntu-vm", "/path/to/disk.vdi", port=0, device=0, type="hdd")
```

### Mount an ISO

```python
manager.mount_iso("ubuntu-vm", "/path/to/ubuntu.iso")
```

## Network Configuration

### Configure Network Adapter

```python
# Configure NAT network
manager.configure_network_adapter(
    vm_name="ubuntu-vm",
    adapter_id=1,
    mode="nat",
    adapter_type="82540EM"
)
```

## Common Tasks

### List All VMs

```python
vms = manager.list_vms()
for vm in vms:
    print(f"Name: {vm['name']}, State: {vm['state']}")
```

### Get VM Information

```python
vm_info = manager.get_vm_info("ubuntu-vm")
print(f"CPU: {vm_info['cpu_count']}")
print(f"Memory: {vm_info['memory_mb']}MB")
print(f"State: {vm_info['state']}")
```

## Next Steps

- [Advanced Usage](../advanced/)
- [API Reference](../api/)
- [Configuration Guide](../advanced/configuration.md)



