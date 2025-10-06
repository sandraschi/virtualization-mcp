# Development Environment Setup Workflow

This guide walks through setting up a complete development environment using vboxmcp, including VM creation, network configuration, and shared folders.

## Prerequisites

- vboxmcp installed and configured
- VirtualBox 7.0+ installed
- Sufficient disk space for VMs
- Development ISO (e.g., Ubuntu Server)

## Step 1: Create a Base Development VM

```python
from vboxmcp import VBoxManager

# Initialize the manager
manager = VBoxManager()

# Create a base development VM
vm_config = {
    "name": "dev-base",
    "os_type": "Ubuntu_64",
    "memory_mb": 8192,          # 8GB RAM
    "cpus": 4,                  # 4 vCPUs
    "storage_gb": 50,           # 50GB disk
    "firmware": "efi",         # UEFI firmware
    "chipset": "ich9",         # Modern chipset
    "nested_virt": True,       # For Docker/K8s
    "vtx_vpid": True,          # Hardware virtualization
    "vtx_ux": True,            # Unrestricted guest
    "audio": False,            # Disable audio
    "usb": False,              # Disable USB
    "clipboard": "bidirectional",
    "dragndrop": "bidirectional"
}

# Create the VM
vm = manager.create_vm(vm_config)

# Add a SATA controller for better performance
manager.add_storage_controller(
    vm_name="dev-base",
    name="SATA Controller",
    controller_type="sata",
    port_count=4,
    bootable=True,
    use_host_io_cache=True
)

# Create and attach a disk
manager.create_disk(
    path=f"{manager.get_vm_folder('dev-base')}/disk.vdi",
    size_gb=50,
    format="vdi",
    variant="standard"
)

manager.attach_disk(
    vm_name="dev-base",
    disk_path=f"{manager.get_vm_folder('dev-base')}/disk.vdi",
    controller="SATA Controller",
    port=0,
    device=0,
    disk_type="hdd"
)

# Configure network
manager.configure_network_adapter(
    vm_name="dev-base",
    adapter_id=1,
    mode="nat",
    adapter_type="82540EM",
    cable_connected=True
)

# Add port forwarding for SSH
manager.add_port_forwarding(
    vm_name="dev-base",
    rule_name="SSH",
    protocol="tcp",
    host_port=2222,
    guest_port=22
)
```

## Step 2: Install the Operating System

```python
# Mount the installation ISO
manager.mount_iso(
    vm_name="dev-base",
    iso_path="/path/to/ubuntu-server-22.04.iso",
    controller="IDE Controller",
    port=1,
    device=0
)

# Set the boot order to boot from CD first
manager.set_boot_order("dev-base", ["dvd", "disk", "none", "none"])

# Start the VM in headless mode
manager.start_vm("dev-base", gui=False, headless=True)

# Wait for installation to complete (monitor console output)
# After installation is complete, power off the VM
manager.stop_vm("dev-base")

# Unmount the installation ISO
manager.unmount_iso("dev-base")

# Set the boot order back to disk first
manager.set_boot_order("dev-base", ["disk", "none", "none", "none"])
```

## Step 3: Configure Shared Folders

```python
# Add shared folders for development
shared_folders = {
    "projects": "/path/to/your/projects",
    "configs": "/path/to/your/configs"
}

for name, host_path in shared_folders.items():
    manager.add_shared_folder(
        vm_name="dev-base",
        name=name,
        host_path=host_path,
        auto_mount=True,
        permanent=True
    )

# Configure auto-mount settings
manager.configure_shared_folder_automount(
    vm_name="dev-base",
    auto_mount=True,
    mount_point="/mnt/shared"
)
```

## Step 4: Take a Base Snapshot

```python
# Take a snapshot of the clean installation
manager.create_snapshot(
    vm_name="dev-base",
    snapshot_name="base-install",
    description="Fresh OS installation with basic configuration"
)
```

## Step 5: Install Development Tools

```python
# Start the VM
manager.start_vm("dev-base")

# Execute commands to install development tools
# This is a simplified example - you would typically use SSH
commands = [
    "sudo apt update",
    "sudo apt upgrade -y",
    "sudo apt install -y git curl wget build-essential",
    # Add your development tools here
    "# Install Docker",
    "curl -fsSL https://get.docker.com -o get-docker.sh",
    "sudo sh get-docker.sh",
    "sudo usermod -aG docker $USER",
    
    "# Install VS Code Server",
    "curl -fsSL https://code-server.dev/install.sh | sh",
    "sudo systemctl enable --now code-server@$USER",
    
    "# Configure shared folders in fstab",
    "echo 'projects /mnt/shared/projects vboxsf defaults,uid=1000,gid=1000,dmode=755,fmode=644 0 0' | sudo tee -a /etc/fstab",
    "echo 'configs /mnt/shared/configs vboxsf defaults,uid=1000,gid=1000,dmode=755,fmode=644 0 0' | sudo tee -a /etc/fstab"
]

for cmd in commands:
    if not cmd.startswith('#'):
        manager.execute_command("dev-base", cmd)

# Reboot the VM to apply changes
manager.reboot_vm("dev-base")
```

## Step 6: Take a Development Environment Snapshot

```python
# Take a snapshot with development tools installed
manager.create_snapshot(
    vm_name="dev-base",
    snapshot_name="dev-tools-installed",
    description="Development environment with all tools installed"
)
```

## Step 7: Create a Clone for a Specific Project

```python
# Create a linked clone for a specific project
project_name = "my-project"
manager.clone_vm(
    source_vm="dev-base",
    new_vm_name=f"dev-{project_name}",
    mode="linked",
    snapshot_name="dev-tools-installed"
)

# Configure project-specific settings
manager.modify_vm(f"dev-{project_name}", {
    "memory_mb": 12288,  # 12GB for this project
    "cpus": 6,          # 6 vCPUs
    "description": f"Development environment for {project_name}"
})
```

## Step 8: Start Development

```python
# Start the project VM
manager.start_vm(f"dev-{project_name}")

# The VM is now ready for development with:
# - SSH access via localhost:2222
# - VS Code Server running on port 8080
# - Shared folders for project files
# - All development tools pre-installed
```

## Maintenance and Updates

### Updating the Base Image

```python
# Restore the base VM to the clean state
manager.restore_snapshot("dev-base", "base-install")

# Start the VM and apply updates
manager.start_vm("dev-base")

# Run update commands
update_commands = [
    "sudo apt update",
    "sudo apt upgrade -y",
    "sudo apt autoremove -y"
]

for cmd in update_commands:
    manager.execute_command("dev-base", cmd)

# Take a new snapshot
manager.create_snapshot(
    vm_name="dev-base",
    snapshot_name=f"base-updated-{datetime.now().strftime('%Y%m%d')}",
    description=f"Updated base image on {datetime.now().strftime('%Y-%m-%d')}"
)
```

### Creating New Project Environments

```python
def create_project_environment(project_name, memory_mb=8192, cpus=4):
    """Create a new development environment for a project."""
    # Create a linked clone from the latest snapshot
    manager.clone_vm(
        source_vm="dev-base",
        new_vm_name=f"dev-{project_name}",
        mode="linked",
        snapshot_name=None  # Use current state
    )
    
    # Configure resources
    manager.modify_vm(f"dev-{project_name}", {
        "memory_mb": memory_mb,
        "cpus": cpus,
        "description": f"Development environment for {project_name}"
    })
    
    # Add project-specific shared folders
    manager.add_shared_folder(
        vm_name=f"dev-{project_name}",
        name=project_name,
        host_path=f"/path/to/projects/{project_name}",
        auto_mount=True,
        permanent=True
    )
    
    return f"dev-{project_name}"

# Example usage
project_vm = create_project_environment("new-project", memory_mb=16384, cpus=8)
manager.start_vm(project_vm)
```

## Troubleshooting

### Common Issues

1. **Shared Folders Not Mounting**
   - Ensure VirtualBox Guest Additions are installed
   - Check the VM's shared folder settings
   - Verify the mount point exists and has proper permissions

2. **Network Connectivity**
   - Check the VM's network adapter settings
   - Verify the host's firewall isn't blocking connections
   - Ensure the VM has a valid IP address

3. **Performance Issues**
   - Allocate more CPU/memory if available
   - Enable 3D acceleration if using a GUI
   - Consider using a different disk controller type

## Next Steps

- [Advanced Configuration](../advanced/performance_tuning.md)
- [Security Best Practices](../advanced/security.md)
- [Backup and Recovery](../examples/workflows/backup_recovery.md)
