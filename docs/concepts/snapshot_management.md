# Snapshot Management

## Overview

vboxmcp provides comprehensive snapshot management capabilities, allowing you to capture and restore the complete state of a virtual machine at any point in time.

## Core Operations

### Creating Snapshots

```python
# Create a basic snapshot
manager.create_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="clean-install",
    description="Fresh OS installation"
)

# Create a snapshot with memory state
manager.create_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="running-state",
    description="Running state with active applications",
    include_ram=True,  # Include RAM state
    pause_vm=False     # Don't pause VM during snapshot
)
```

### Listing Snapshots

```python
# List all snapshots for a VM
snapshots = manager.list_snapshots("ubuntu-server")

# Get detailed information about a specific snapshot
snapshot_info = manager.get_snapshot_info(
    vm_name="ubuntu-server",
    snapshot_name="clean-install"
)
```

### Restoring Snapshots

```python
# Restore a snapshot (power off VM if running)
manager.restore_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="clean-install"
)

# Restore and start the VM
manager.restore_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="clean-install",
    start_vm=True
)
```

### Deleting Snapshots

```python
# Delete a specific snapshot
manager.delete_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="old-snapshot"
)

# Delete all snapshots (consolidate disk)
manager.delete_all_snapshots("ubuntu-server")
```

## Advanced Operations

### Snapshot Branching

```python
# Create a new branch from an existing snapshot
manager.create_snapshot_branch(
    vm_name="ubuntu-server",
    base_snapshot="base-install",
    new_branch_name="experimental-feature"
)

# Create a new snapshot on a specific branch
manager.create_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="feature-update-1",
    parent_snapshot="experimental-feature"
)
```

### Snapshot Properties

```python
# Get snapshot properties
properties = manager.get_snapshot_properties(
    vm_name="ubuntu-server",
    snapshot_name="clean-install"
)

# Update snapshot properties
manager.update_snapshot_properties(
    vm_name="ubuntu-server",
    snapshot_name="clean-install",
    properties={
        "description": "Updated description",
        "timestamp": "2023-01-01T00:00:00Z"
    }
)
```

### Snapshot Disk Management

```python
# Get disk usage for snapshots
disk_usage = manager.get_snapshot_disk_usage("ubuntu-server")

# Compact snapshot storage
manager.compact_snapshot_storage("ubuntu-server")

# Export a snapshot to a file
manager.export_snapshot(
    vm_name="ubuntu-server",
    snapshot_name="clean-install",
    output_file="/path/to/export.ova"
)
```

## Best Practices

1. **Naming Conventions**
   - Use descriptive names and timestamps
   - Include version numbers for application states
   - Document the purpose of each snapshot

2. **Snapshot Frequency**
   - Take snapshots before major changes
   - Create regular checkpoints during development
   - Avoid excessive snapshots to save disk space

3. **Performance Considerations**
   - Snapshots with RAM are larger but capture the full state
   - Disk-only snapshots are smaller but require a clean boot
   - Regularly delete unused snapshots to free up space

4. **Backup Strategy**
   - Export important snapshots as OVA files
   - Store snapshots on separate storage
   - Test snapshot restoration regularly

## Troubleshooting

### Common Issues

1. **Snapshot Creation Fails**
   - Check available disk space
   - Ensure the VM is in a stable state
   - Verify VirtualBox permissions

2. **Slow VM Performance**
   - Too many snapshots can impact performance
   - Consider consolidating snapshots
   - Check disk fragmentation

3. **Snapshot Restoration Issues**
   - Verify snapshot integrity
   - Check for disk errors
   - Ensure sufficient resources for the snapshot state

## Next Steps

- [Advanced Configuration](../advanced/performance_tuning.md)
- [Security Best Practices](../advanced/security.md)
- [API Reference](../api/)
