# Virtualization-MCP User Prompt Template

## Available Operations

### Virtual Machine Operations
- Create a new ${vm_type} virtual machine
- Start/stop/pause/resume virtual machine "${vm_name}"
- Get information about ${vm_name}
- Delete virtual machine ${vm_name}
- Clone ${source_vm} to create ${new_vm}
- Modify ${vm_name} settings (memory, CPU, network, etc.)

### Snapshot Operations
- Create a snapshot of ${vm_name} named "${snapshot_name}"
- Restore ${vm_name} to snapshot "${snapshot_name}"
- List all snapshots for ${vm_name}
- Delete snapshot "${snapshot_name}" from ${vm_name}

### Network Configuration
- Configure ${adapter_type} network for ${vm_name}
- Set up port forwarding on ${vm_name} (${host_port} → ${guest_port})
- Create host-only network "${network_name}"
- List network adapters for ${vm_name}

### Storage Management
- Attach ${disk_type} disk to ${vm_name}
- Mount ISO "${iso_path}" on ${vm_name}
- Create ${size_gb}GB virtual disk at "${disk_path}"
- List storage controllers for ${vm_name}

### System Information
- Show all virtual machines
- Get host system information
- List available OS types
- Check VirtualBox version

### Backup and Security
- Create backup of ${vm_name}
- Scan ${vm_name} for security issues
- Run ${test_type} security test on ${vm_name}

## Common Workflows

### Setting Up a New VM
1. List available OS types
2. Create VM with appropriate configuration
3. Attach ISO for OS installation
4. Configure network (NAT for internet access)
5. Start VM and install OS
6. Create "Clean Install" snapshot

### Testing Workflow
1. Create VM from template
2. Start VM
3. Run tests
4. Create snapshot if tests pass
5. Delete VM when done

### Development Environment
1. Create base VM with development tools
2. Create snapshot "Dev Environment Base"
3. Clone VM for different projects
4. Use snapshots for quick environment resets

## Examples

- "Create an Ubuntu 22.04 VM with 4GB RAM and 40GB disk"
- "List all running virtual machines"
- "Take a snapshot of DevVM called 'Before Update'"
- "Configure NAT network with port forwarding 8080→80 on WebServer"
- "Clone ProductionVM to create TestVM"
- "Show me the host system information"

