# Storage Management

## Overview

vboxmcp provides comprehensive storage management capabilities for VirtualBox virtual machines, including disk management, storage controllers, and ISO handling.

## Storage Controllers

### Supported Controller Types

- **IDE**: Legacy controller for maximum compatibility
- **SATA (AHCI)**: Recommended for modern OSes
- **SCSI**: For high-performance storage
- **SAS**: For enterprise storage
- **NVMe**: For high-performance SSDs (experimental)
- **Floppy**: For legacy floppy disk support

### Managing Controllers

```python
# Add a storage controller
manager.add_storage_controller(
    vm_name="ubuntu-server",
    name="SATA Controller",
    controller_type="sata",
    port_count=4,
    bootable=True,
    use_host_io_cache=True
)

# List storage controllers
controllers = manager.list_storage_controllers("ubuntu-server")

# Remove a storage controller
manager.remove_storage_controller("ubuntu-server", "SATA Controller")
```

## Virtual Disks

### Disk Formats

- **VDI**: VirtualBox native format
- **VMDK**: VMware compatible format
- **VHD**: Microsoft Virtual PC format
- **RAW**: Raw disk image
- **QCOW2**: QEMU format (limited support)

### Creating Disks

```python
# Create a dynamically allocated disk
manager.create_disk(
    path="/path/to/disk.vdi",
    size_gb=100,
    format="vdi",
    variant="standard"  # or "fixed" for pre-allocated
)

# Create a disk with specific parameters
manager.create_disk(
    path="/path/to/disk.vmdk",
    size_gb=200,
    format="vmdk",
    variant="split2g",  # Split into 2GB files
    medium_type="ssd"   # Mark as SSD
)
```

### Attaching and Detaching Disks

```python
# Attach a disk to a VM
manager.attach_disk(
    vm_name="ubuntu-server",
    disk_path="/path/to/disk.vdi",
    controller="SATA Controller",
    port=1,
    device=0,
    disk_type="hdd"
)

# Detach a disk
manager.detach_disk("ubuntu-server", "SATA Controller", port=1, device=0)

# List attached disks
attached_disks = manager.list_attached_disks("ubuntu-server")
```

### Disk Operations

```python
# Clone a disk
manager.clone_disk(
    source="/path/to/source.vdi",
    target="/path/to/clone.vdi",
    format="vdi",
    variant="standard"
)

# Resize a disk
manager.resize_disk("/path/to/disk.vdi", new_size_gb=200)

# Compact a disk (reclaim unused space)
manager.compact_disk("/path/to/disk.vdi")

# Convert disk format
manager.convert_disk(
    source="/path/to/source.vdi",
    target="/path/to/converted.vmdk",
    target_format="vmdk"
)

# Get disk information
disk_info = manager.get_disk_info("/path/to/disk.vdi")
```

## ISO Management

### Mounting and Unmounting ISOs

```python
# Mount an ISO to a VM's virtual CD/DVD drive
manager.mount_iso(
    vm_name="ubuntu-server",
    iso_path="/path/to/ubuntu.iso",
    controller="IDE Controller",  # Optional
    port=1,                       # Optional
    device=0                      # Optional
)

# Unmount an ISO
manager.unmount_iso("ubuntu-server")

# List mounted media
mounted_media = manager.list_mounted_media("ubuntu-server")
```

### Creating Bootable ISOs

```python
# Create a bootable ISO from files
data = {
    "/boot/grub/grub.cfg": "set default=0\ntimeout=10\nmenuentry 'Boot' {\n    linux /vmlinuz root=/dev/sda1\n    initrd /initrd.img\n}",
    "/vmlinuz": "...binary kernel data...",
    "/initrd.img": "...initramfs data..."
}

manager.create_bootable_iso(
    output_path="/path/to/boot.iso",
    files=data,
    boot_catalog="boot/grub/boot.cat",
    boot_image="boot/grub/eltorito.img"
)
```

## Shared Folders

### Managing Shared Folders

```python
# Add a shared folder
manager.add_shared_folder(
    vm_name="ubuntu-server",
    name="shared_data",
    host_path="/path/on/host",
    auto_mount=True,
    permanent=True
)

# List shared folders
shared_folders = manager.list_shared_folders("ubuntu-server")

# Remove a shared folder
manager.remove_shared_folder("ubuntu-server", "shared_data")
```

### Auto-Mount Configuration

```python
# Configure auto-mount settings
manager.configure_shared_folder_automount(
    vm_name="ubuntu-server",
    auto_mount=True,
    mount_point="/mnt/shared"
)
```

## Best Practices

1. **Disk Management**
   - Use appropriate disk formats for your use case
   - Regularly compact dynamic disks to reclaim space
   - Consider using fixed-size disks for production workloads

2. **Performance**
   - Place VM disks on fast storage (SSD/NVMe)
   - Enable host I/O cache for better performance
   - Consider using paravirtualized storage controllers

3. **Backup**
   - Regularly back up VM disk images
   - Use snapshots for point-in-time recovery
   - Consider using disk image compression for archiving

## Troubleshooting

### Common Issues

1. **Disk Full**
   - Check disk usage with `get_disk_info()`
   - Compact dynamic disks to reclaim space
   - Consider resizing the disk if needed

2. **Performance Problems**
   - Check host disk I/O performance
   - Verify disk controller type matches workload
   - Consider using a different disk format

3. **Mount Issues**
   - Verify ISO file integrity
   - Check VM storage controller configuration
   - Ensure the VM is powered off when changing storage settings

## Next Steps

- [Network Configuration](../concepts/network_configuration.md)
- [Snapshot Management](../concepts/snapshot_management.md)
- [Advanced Configuration](../advanced/performance_tuning.md)
