# Virtual Machine Management

## Overview

virtualization-mcp provides comprehensive management of VirtualBox virtual machines through an intuitive API. This document covers the core VM management capabilities.

## Core Operations

### Creating VMs

```python
# Basic VM creation
vm_config = {
    "name": "ubuntu-server",
    "os_type": "Ubuntu_64",
    "memory_mb": 4096,
    "cpus": 2,
    "storage_gb": 50,
    "network": {
        "adapter1": {
            "enabled": True,
            "type": "nat",
            "adapter_type": "82540EM"
        }
    },
    "storage_controllers": [
        {
            "name": "SATA Controller",
            "type": "sata",
            "port_count": 2,
            "bootable": True
        }
    ]
}

vm = manager.create_vm(vm_config)
```

### Starting and Stopping VMs

```python
# Start a VM
manager.start_vm("ubuntu-server", gui=False, headless=False)

# Stop a VM (graceful shutdown)
manager.stop_vm("ubuntu-server")

# Force stop a VM
manager.stop_vm("ubuntu-server", force=True)

# Reset a VM (hard reset)
manager.reset_vm("ubuntu-server")

# Pause/Resume a VM
manager.pause_vm("ubuntu-server")
manager.resume_vm("ubuntu-server")
```

### Cloning VMs

```python
# Full clone with new MAC addresses
manager.clone_vm("ubuntu-server", "ubuntu-server-clone", mode="full")

# Linked clone (saves disk space)
manager.clone_vm("ubuntu-server", "ubuntu-server-linked", mode="linked")
```

### Deleting VMs

```python
# Delete a VM and all its files
manager.delete_vm("ubuntu-server-clone", delete_files=True)
```

## Advanced VM Configuration

### Modifying VM Settings

```python
# Update VM resources
manager.modify_vm("ubuntu-server", {
    "memory_mb": 8192,
    "cpus": 4,
    "nested_virt": True,
    "paravirt_provider": "kvm"
})

# Configure CPU execution cap
manager.set_cpu_cap("ubuntu-server", 90)  # 90% CPU cap

# Enable/disable features
manager.enable_feature("ubuntu-server", "io_apic")
manager.disable_feature("ubuntu-server", "audio")
```

### Managing VM Groups

```python
# Create a group
manager.create_group("development")

# Add VMs to a group
manager.add_vm_to_group("ubuntu-server", "development")
manager.add_vm_to_group("ubuntu-server-clone", "development")

# List VMs in a group
vms = manager.list_vms_in_group("development")

# Remove VM from group
manager.remove_vm_from_group("ubuntu-server-clone", "development")
```

## VM Information and Monitoring

### Getting VM Information

```python
# Get basic VM info
vm_info = manager.get_vm_info("ubuntu-server")

# Get detailed VM configuration
vm_config = manager.get_vm_config("ubuntu-server")

# Get VM metrics (CPU, memory, disk I/O, etc.)
metrics = manager.get_vm_metrics("ubuntu-server")

# Check if VM is running
is_running = manager.is_vm_running("ubuntu-server")
```

### Monitoring VM Console

```python
# Get console output (for headless VMs)
console_output = manager.get_console_output("ubuntu-server")

# Take a screenshot
screenshot = manager.take_screenshot("ubuntu-server", "/path/to/save.png")
```

## Best Practices

1. **Resource Allocation**
   - Allocate only the resources your VM needs
   - Leave enough resources for the host system
   - Consider CPU pinning for performance-critical VMs

2. **VM Organization**
   - Use meaningful names and descriptions
   - Group related VMs together
   - Document VM purposes and configurations

3. **Backup Strategy**
   - Take regular snapshots before major changes
   - Export VMs for long-term storage
   - Consider using linked clones for testing

4. **Security**
   - Keep guest additions up to date
   - Use secure boot when possible
   - Isolate network traffic as needed

## Troubleshooting

### Common Issues

1. **VM Won't Start**
   - Check VirtualBox logs
   - Verify VT-x/AMD-V is enabled in BIOS
   - Ensure enough system resources are available

2. **Network Connectivity Issues**
   - Verify network adapter settings
   - Check firewall rules
   - Test with different network modes

3. **Performance Problems**
   - Check host system resource usage
   - Verify disk I/O performance
   - Consider enabling nested virtualization if needed

## Next Steps

- [Storage Management](../concepts/storage_management.md)
- [Network Configuration](../concepts/network_configuration.md)
- [Snapshot Management](../concepts/snapshot_management.md)



