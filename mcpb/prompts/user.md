# Virtualization-MCP User Guide & Tutorials

## Getting Started

Virtualization-MCP gives you complete control over VirtualBox and Hyper-V virtual machines, Docker containers, Windows Sandbox environments, and network configurations through natural language commands. This guide walks through everything from basic VM creation to advanced multi-machine orchestration.

## 1. VM Management Tutorial

### 1.1 Creating Your First Virtual Machine

The most common operation is creating a VM. Start by checking available OS types:

```
List available OS types
```

This shows all supported guest operating systems. For an Ubuntu desktop VM, the type would be "Ubuntu_64". Now create it:

```
Create a virtual machine named "Ubuntu-Desktop" with Ubuntu_64, 4GB RAM, 2 CPUs, 40GB disk
```

The server allocates resources and registers the VM with VirtualBox. You can verify it exists:

```
Show all VMs
```

During creation, the server automatically sets up a SATA controller for the virtual disk and an IDE controller for CD/DVD. The VM starts in powered-off state, ready for OS installation.

### 1.2 Installing an Operating System

Mount an installation ISO:

```
Mount the ISO file /home/user/ubuntu-24.04-desktop.iso on Ubuntu-Desktop
```

Start the VM in GUI mode:

```
Start Ubuntu-Desktop in gui mode
```

A VirtualBox window opens showing the OS installer. Complete the installation interactively. After the OS is installed and the VM shuts down, create a snapshot:

```
Take a snapshot of Ubuntu-Desktop called "Clean Install"
```

This preserves the fresh OS state for quick rollback.

### 1.3 Starting, Stopping, and Managing VM State

VMs have multiple power states: poweroff, running, paused, saved, and aborted. Each state enables different operations:

```
Start Ubuntu-Desktop                    # Boot the VM
Pause Ubuntu-Desktop                    # Freeze execution instantly
Resume Ubuntu-Desktop                   # Unfreeze and continue
```

To stop a running VM, you have options:

```
Power off Ubuntu-Desktop                # Force shutdown (like unplugging)
Save state Ubuntu-Desktop               # Freeze to disk, resume later
ACPI shutdown Ubuntu-Desktop            # Graceful shutdown (presses power button)
```

Save state is especially useful for development VMs -- no boot time on resume. For servers, always prefer ACPI shutdown to avoid filesystem corruption.

### 1.4 Modifying VM Configuration

VMs can be reconfigured after creation. Changes to CPU and memory require the VM to be powered off:

```
Modify Ubuntu-Desktop: set 8192 MB RAM, 4 CPUs
Modify Ubuntu-Desktop: enable PAE/NX, enable VT-x/AMD-V
```

Other settings can be changed while the VM is running using online-resize-capable values:

```
Modify Ubuntu-Desktop: set 256 MB video memory
Modify Ubuntu-Desktop: set graphics controller to VMSVGA
```

### 1.5 Cloning VMs

Cloning creates a copy of an existing VM. Two clone types exist:

Full clone -- independent copy that shares nothing with the source:
```
Clone Ubuntu-Desktop to Ubuntu-Dev-Environment with full clone type
```

Linked clone -- depends on the source's base disk, saving disk space:
```
Clone Ubuntu-Desktop to Ubuntu-Test-Environment with linked clone type
```

Linked clones are ideal for test environments where you want many VMs from one base. Full clones are safer for production since they are fully independent.

### 1.6 Deleting VMs

When a VM is no longer needed:

```
Delete Ubuntu-Test-Environment
```

By default, VirtualBox deletes the VM configuration but keeps the disk files. Add the --delete-disk flag to also remove virtual disks:

```
Delete Ubuntu-Test-Environment with disk deletion
```

Always verify which VMs exist before deletion:

```
List all VMs
```

## 2. Snapshot Operations Tutorial

### 2.1 Understanding Snapshots

Snapshots capture a VM's complete state at a point in time: disk contents, memory contents (if taken while running), and VM configuration. They are stored as a tree -- each snapshot can have children, forming a hierarchy.

Use snapshots as save points before risky operations:

- Before installing updates
- Before configuration changes
- Before testing new software
- As clean-state markers for testing

### 2.2 Creating Snapshots

Basic snapshot creation:

```
Create snapshot "Before-Kernel-Update" on Ubuntu-Desktop
```

For running VMs, include memory state for instant restore:

```
Create snapshot "Stable-State" on Ubuntu-Desktop with memory
```

Follow a naming convention for clarity:

- "Clean-Install" for fresh OS
- "Before-Update-{date}" before updates
- "Stable-Baseline" for known-good configs
- "Before-Experiment" before risky changes

### 2.3 Viewing Snapshot Trees

List all snapshots with their hierarchy:

```
List snapshots for Ubuntu-Desktop
```

Output shows the snapshot tree with indentation indicating parent-child relationships, creation dates, and descriptions.

### 2.4 Restoring Snapshots

Roll back to a previous state:

```
Restore snapshot "Before-Kernel-Update" on Ubuntu-Desktop
```

Restoring reverts disk contents and, if the snapshot includes memory, the VM's exact running state. The VM returns to the state it was in when the snapshot was taken.

To restore and keep the current state as a child snapshot (so you can go back to it):

```
Restore snapshot "Stable-Baseline" on Ubuntu-Desktop with keep current state
```

### 2.5 Deleting Snapshots

Remove unnecessary snapshots to free disk space:

```
Delete snapshot "Temp-Test-State" from Ubuntu-Desktop
```

Deleting a snapshot merges its disk differences into the parent snapshot. The VM's current state is preserved. Deleting the root snapshot merges all changes.

### 2.6 Snapshot Best Practices

- Keep 3-5 snapshots per VM maximum (too many consume disk space)
- Always name snapshots descriptively -- "Snapshot 1" is useless
- Before deleting a VM, check snapshot disk usage
- Use snapshots with linked clones for efficient testing
- Take a snapshot immediately after OS installation and guest additions

## 3. Network Configuration Tutorial

### 3.1 Network Adapter Types

VirtualBox supports six network attachment modes, each with different connectivity characteristics:

NAT (default): VM can access the internet through the host. Host and other VMs cannot initiate connections to the VM without port forwarding. Best for: single VMs needing internet access.

Bridged: VM appears as a separate device on the physical network, getting its own IP from the network DHCP. Best for: servers that need full network presence.

Host-Only: VM communicates only with the host and other VMs on the same host-only network. No external access. Best for: isolated test environments.

Internal: VM communicates only with other VMs on the same internal network. Not even the host can connect. Best for: multi-VM private networks.

NAT Network: Like NAT but VMs can talk to each other on the same NAT network. Best for: multi-VM setups with shared internet.

Generic: Connects to user-configured UDP/Tunnel networks. Best for: advanced network topologies.

### 3.2 Configuring Network Adapters

Add a NAT adapter for internet access:

```
Configure Ubuntu-Desktop with NAT adapter
```

For a web server that needs local network presence, use bridged:

```
Configure WebServer with bridged adapter on "Realtek PCIe GbE Family Controller"
```

Create an isolated test network:

```
Create host-only network "Test-Network" with IP 192.168.100.1/24
Configure TestVM with host-only adapter on "Test-Network"
```

### 3.3 Port Forwarding

Port forwarding allows host-to-VM connections through a NAT adapter:

```
Add port forwarding rule on Ubuntu-Desktop: SSH, host port 2222 to guest port 22, TCP
Add port forwarding rule on Ubuntu-Desktop: Web, host port 8080 to guest port 80, TCP
Add port forwarding rule on Ubuntu-Desktop: HTTPS, host port 8443 to guest port 443, TCP
```

After configuration, access services at:
- SSH: ssh -p 2222 user@localhost
- Web: http://localhost:8080
- HTTPS: https://localhost:8443

To list existing rules:

```
List port forwarding rules on Ubuntu-Desktop
```

### 3.4 Multi-Network VMs

VMs can have up to 4 network adapters, each on a different network:

```
Configure Ubuntu-Desktop:
  Adapter 1: NAT for internet
  Adapter 2: host-only on "Test-Network" for inter-VM communication
  Adapter 3: internal on "Private-Network" for isolated services
```

This setup is common for development environments where the VM needs internet access (NAT), communication with other VMs (host-only), and isolated services (internal).

### 3.5 Network Troubleshooting

Check adapter status:

```
Show network info for Ubuntu-Desktop
```

Common issues:
- No internet: verify NAT adapter is enabled and cable connected
- No host-only connectivity: ensure host-only network exists
- Port forwarding not working: verify VM is running and service is listening on guest port
- IP conflicts: check if bridged adapter has unique MAC

## 4. Storage Management Tutorial

### 4.1 Storage Controllers

VMs support multiple storage controller types:

- IDE (PIIX4, ICH6): Legacy, 2 devices per controller. Best for CD/DVD and older OSes.
- SATA (AHCI): Modern, up to 30 devices. Default for most VMs.
- SCSI (BusLogic, LSI Logic): High-performance, up to 15 devices.
- NVMe: Fastest, for modern OSes with NVMe drivers.

### 4.2 Attaching and Detaching Disks

Add an existing virtual disk to a VM:

```
Attach disk /path/to/data.vdi to Ubuntu-Desktop on SATA controller port 1
```

Detach a disk:

```
Detach disk from Ubuntu-Desktop on SATA controller port 1
```

Create a new data disk and attach it:

```
Create 100 GB VDI disk at /home/user/VirtualBox VMs/Ubuntu-Desktop/data.vdi
Attach disk /home/user/VirtualBox VMs/Ubuntu-Desktop/data.vdi to Ubuntu-Desktop on SATA port 2
```

### 4.3 ISO Management

Mount an ISO file for OS installation or add-on installation:

```
Mount ISO /home/user/ubuntu-24.04-desktop.iso on Ubuntu-Desktop
```

Mount Guest Additions:

```
Mount ISO /usr/share/virtualbox/VBoxGuestAdditions.iso on Ubuntu-Desktop
```

Eject when done:

```
Unmount ISO from Ubuntu-Desktop
```

### 4.4 Creating Virtual Disks

Create disks in different formats:

```
Create 50 GB VDI disk at /path/to/disk.vdi        # VirtualBox native format
Create 50 GB VMDK disk at /path/to/disk.vmdk       # VMware compatible
Create 50 GB VHD disk at /path/to/disk.vhd         # Microsoft Hyper-V compatible
```

Disk variants:
- Standard (default): dynamically allocated, grows as data is written
- Fixed: pre-allocated, faster IO but uses full size immediately
- Differencing: stores changes relative to a parent disk, for snapshot-like behavior

### 4.5 Storage Controller Management

Add more controllers when you need additional ports:

```
Create USB controller on Ubuntu-Desktop
Add SATA controller on Ubuntu-Desktop
```

List existing controllers:

```
List storage controllers on Ubuntu-Desktop
```

## 5. Container Orchestration Tutorial

### 5.1 Docker Sandbox Basics

Virtualization-MCP provides Docker-based sandbox environments for running code in isolated containers:

```
Create sandbox "test-python" with python:3.12 image with host code execution
```

This starts a container with a Python 3.12 environment. You can execute code inside it:

```
Run echo "Hello from Docker sandbox" in sandbox "test-python"
```

### 5.2 Portfolio-Managed Sandboxes

Portfolios are predefined groups of sandbox configurations that automate setup:

```
Create sandbox from portfolio "web-development" with WebApp portfolio
```

This automatically creates a sandbox with:
- Required tools (Node.js, npm, git)
- Pre-loaded project files
- Network configuration
- Startup scripts
- File mounts from host

### 5.3 Sandbox Lifecycle Management

```
List active sandboxes
Get sandbox info for sandbox "test-python"
Stop sandbox "test-python"
Delete sandbox "test-python"
```

Sandbox directories are automatically cleaned up on deletion. Each sandbox gets a unique state file tracking its configuration, creation time, and status.

### 5.4 Host File Execution

Run files from the host filesystem inside a throwaway container:

```
Run host file /home/user/scripts/deploy.py on python:3.12-alpine
```

The file is automatically uploaded to the container, executed, and the container is removed. This is ideal for:
- Testing deployment scripts
- Running analysis in isolated environments
- Executing code with specific runtime requirements

### 5.5 Windows Sandbox Integration

On Windows 10/11 Pro and Enterprise, Windows Sandbox provides lightweight virtualization:

```
Create Windows sandbox "test-app" with shared folder C:\Projects
```

Windows Sandbox features:
- One-click disposable Windows environments
- Shared folders for file exchange
- Startup scripts for automation
- Automatic cleanup on close
- No VHD management needed

To configure advanced Windows Sandbox:

```
Create Windows sandbox "dev-test" with:
  - Shared folder: C:\Code
  - Shared folder: C:\Data (read-only)
  - GPU redirection: enabled (if available)
  - Networking: enabled
  - Audio: disabled (headless)
  - Startup command: C:\init.bat
```

### 5.6 Container Networking

Containers can be networked together:

```
Create sandbox "backend" with node:20 image
Create sandbox "frontend" with nginx image
Connect sandbox "backend" to network "app-network"
Connect sandbox "frontend" to network "app-network"
```

This enables inter-container communication while maintaining isolation from other networks.

## 6. Template Creation Tutorial

### 6.1 Creating Templates from Existing VMs

Templates capture a VM's configuration for reuse:

```
Create template from Ubuntu-Desktop named "Ubuntu-Dev-Base"
```

The template stores:
- OS type and architecture
- Memory, CPU, and video configuration
- Storage controller layout
- Network adapter configuration
- Audio and USB settings
- Metadata including description, version, and tags

### 6.2 Deploying from Templates

Create new VMs from templates with a single command:

```
Deploy from template "Ubuntu-Dev-Base" as "Project-1-Dev" with 8192 MB RAM
Deploy from template "Ubuntu-Dev-Base" as "Project-2-Dev" with 4096 MB RAM
```

Template deployment automatically:
1. Loads the template configuration
2. Creates the VM with inherited settings
3. Overrides any custom parameters (memory, CPU, etc.)
4. Registers the new VM in VirtualBox

### 6.3 Managing Templates

```
List all templates
Show template info for "Ubuntu-Dev-Base"
Update template "Ubuntu-Dev-Base" with new description "Updated dev environment"
Delete template "Ubuntu-Dev-Base"
```

### 6.4 Template Workflows

Template-based team development workflow:

```
# Admin creates golden image template
Create template from "Golden-Workstation" named "Dev-Standard"

# Team members deploy from template
Deploy from template "Dev-Standard" as "Alice-DevBox"
Deploy from template "Dev-Standard" as "Bob-DevBox"

# Apply updates to template
Modify template "Dev-Standard" update memory to 16 GB

# Old templates retired
Delete template "Dev-Standard-v1"
```

## 7. Resource Monitoring Tutorial

### 7.1 Host System Information

Get a complete overview of the host system:

```
Show host system information
```

This returns:
- Operating system: Windows 11 Pro / Ubuntu 24.04
- CPU: model, cores, threads, utilization percentage
- Memory: total, used, available, percentage
- Disk: total space, used space, free space
- VirtualBox version and installation status

### 7.2 VM Performance Metrics

Monitor individual VM resource usage:

```
Get performance metrics for Ubuntu-Desktop
```

Metrics include:
- CPU usage percentage
- Memory allocation vs. usage
- Disk I/O operations
- Network throughput
- Up time

### 7.3 Health Checks

Verify the virtualization environment is working:

```
Run health check
```

The health check validates:
- VirtualBox installation and version
- VBoxManage CLI availability
- VM registration and state
- Storage accessibility
- Network adapter availability
- Host resource sufficiency

### 7.4 Backup Management

Create backups before making changes:

```
Create backup of Ubuntu-Desktop
List backups
Restore backup of Ubuntu-Desktop from 2025-10-15
```

Backups store:
- VM configuration (OVF)
- Disk files (VMDK/VHD format)
- Snapshot tree
- Metadata and timestamps

For automated backup scheduling:

```
Configure backup schedule for Ubuntu-Desktop: daily at 02:00, keep 7 backups
```

## 8. Hyper-V Integration Tutorial

### 8.1 Basic Hyper-V Operations

On Windows systems, Virtualization-MCP also manages Hyper-V VMs:

```
List Hyper-V VMs
Get Hyper-V info for "Windows-Server-2022"
Start Hyper-V VM "Windows-Server-2022"
Stop Hyper-V VM "Windows-Server-2022"
```

Hyper-V VM states differ from VirtualBox:
- Running: VM is active
- Off: VM is shut down
- Saved: VM state persisted to disk
- Paused: VM execution frozen

### 8.2 Cross-Hypervisor Management

Manage both VirtualBox and Hyper-V VMs from one interface:

```
Show all VMs                          # Shows both VirtualBox and Hyper-V
```

Results include the hypervisor type for each VM, allowing unified management across virtualization platforms.

## 9. Security and Testing Tutorial

### 9.1 Security Scanning

Scan VMs for security vulnerabilities:

```
Scan Ubuntu-Desktop for security issues
```

Security scans check for:
- Open ports and exposed services
- Outdated software versions
- Weak password configurations
- Missing security patches
- Suspicious processes

### 9.2 Malware Analysis

Analyze VM disks for potential threats:

```
Analyze disk of Ubuntu-Desktop for malware
```

The analysis:
- Scans files for known malware signatures
- Checks for suspicious file patterns
- Identifies potentially unwanted programs
- Generates a threat report with severity levels

### 9.3 Testing Workflows

Complete security testing workflow:

```
# Create isolated test environment
Create sandbox "security-test" for malware analysis

# Run security assessments
Run penetration test on "security-test"
Run vulnerability scan on "security-test"

# Analyze results
Get security report for "security-test"

# Clean up
Delete sandbox "security-test"
```

## 10. Portmanteau Tools Tutorial

Portmanteau tools combine multiple related operations into a single command, reducing the number of tool calls needed:

### 10.1 System Portmanteau

```
system_management get:host_info                       # Single system info call
system_management get:vbox_version                    # Check VirtualBox version
system_management list:ostypes                        # List available OS types
```

### 10.2 VM Portmanteau

```
vm_management create:name=WebServer,ostype=Ubuntu_64,memory=4096,cpu=2,disk=40
vm_management list:filter=running                     # List only running VMs
vm_management info:name=Ubuntu-Desktop                # Full VM details
vm_management start:name=WebServer,mode=headless      # Start in headless mode
vm_management stop:name=WebServer                     # Power off
vm_management delete:name=WebServer                   # Remove VM
```

### 10.3 Snapshot Portmanteau

```
snapshot_management create:vm=Ubuntu-Desktop,name=Before-Update
snapshot_management list:vm=Ubuntu-Desktop             # Full tree view
snapshot_management restore:vm=Ubuntu-Desktop,name=Stable-Baseline
snapshot_management delete:vm=Ubuntu-Desktop,name=Temp-State
```

### 10.4 Network Portmanteau

```
network_management create:nat,vm=Ubuntu-Desktop        # Add NAT adapter
network_management create:hostonly,vm=Ubuntu-Desktop   # Add host-only
network_management portforward:vm=WebServer,host=8080,guest=80
network_management info:vm=Ubuntu-Desktop              # All adapters
```

### 10.5 Storage Portmanteau

```
storage_management attach:vm=Ubuntu-Desktop,disk=data.vdi
storage_management mount:iso=ubuntu.iso,vm=Ubuntu-Desktop
storage_management create_disk:size=100,path=data.vdi
storage_management controllers:vm=Ubuntu-Desktop       # List controllers
```

## 11. Complete Example Workflows

### 11.1 Development Environment Setup (Full Stack)

Step-by-step creation of a complete development environment:

```
# 1. List available OS types
List OS types

# 2. Create development VM
Create VM named "FullStack-Dev" with Ubuntu_64, 8 GB RAM, 4 CPUs, 60 GB disk

# 3. Configure networking (NAT + Host-Only)
Configure FullStack-Dev with NAT adapter
Configure FullStack-Dev with host-only adapter
Add port forwarding: host 2222 to guest 22 on FullStack-Dev

# 4. Start VM and install OS
FullStack-Dev with GUI mode

# 5. After installation, take baseline snapshot
Create snapshot "Clean-Install" on FullStack-Dev with memory

# 6. Install development tools
Mount ISO dev-tools.iso on FullStack-Dev
Create snapshot "Dev-Tools-Installed" on FullStack-Dev

# 7. Create linked clones for projects
Clone FullStack-Dev to Frontend-Project with linked clone
Clone FullStack-Dev to Backend-Project with linked clone
Clone FullStack-Dev to DevOps-Project with linked clone

# 8. Create template for future developers
Create template from FullStack-Dev named "Dev-Standard"
```

### 11.2 Production Web Server Setup

```
# Create web server VM
Create VM named "WebServer-Prod" with UbuntuServer_64, 4 GB RAM, 2 CPUs, 40 GB disk
Configure WebServer-Prod with bridged adapter
Add port forwarding: host 443 to guest 443 on WebServer-Prod

# Install and configure
Start WebServer-Prod with GUI mode
# ... install Nginx/Apache inside VM ...

# Protect with snapshot
Create snapshot "Production-Config" on WebServer-Prod

# Monitor
Get performance metrics for WebServer-Prod
```

### 11.3 Testing and QA Environment

```
# Create base test VM
Create VM from template "Dev-Standard" as "QA-Test-Runner"

# Run security tests
Scan QA-Test-Runner for security issues

# Run malware analysis
Analyze disk of QA-Test-Runner for malware

# Take test pass snapshot
Create snapshot "Pre-Update-Test" on QA-Test-Runner

# Clean up
Delete QA-Test-Runner
```

### 11.4 Disaster Recovery

```
# Before any major change
Create snapshot "Pre-Update-2025-10-15" on Production-Web
Create backup of Production-Web

# If update fails
Restore snapshot "Pre-Update-2025-10-15" on Production-Web

# Or from backup
Restore backup of Production-Web from 2025-10-15
```

### 11.5 Multi-Machine Lab Environment

```
# Create isolated network
Create host-only network "Lab-Network" with IP 10.0.100.1/24

# Create lab machines
Create VM "Lab-DB" with UbuntuServer_64, 2 GB RAM, 1 CPU, 20 GB disk
Create VM "Lab-App" with UbuntuServer_64, 4 GB RAM, 2 CPUs, 30 GB disk
Create VM "Lab-Web" with UbuntuServer_64, 2 GB RAM, 1 CPU, 20 GB disk

# Connect all to same network
Configure Lab-DB with host-only adapter on "Lab-Network"
Configure Lab-App with host-only adapter on "Lab-Network"
Configure Lab-Web with host-only adapter on "Lab-Network"

# Add internet access for updates
Configure Lab-DB with NAT adapter
Configure Lab-App with NAT adapter
Configure Lab-Web with NAT adapter

# Start all VMs
Start Lab-DB with headless mode
Start Lab-App with headless mode
Start Lab-Web with headless mode
```

## 12. Troubleshooting Guide

### 12.1 Common Errors and Solutions

VM won't start:
- Check if VT-x/AMD-V is enabled in BIOS/UEFI
- Ensure Hyper-V is not conflicting (disable Windows Hyper-V if using VirtualBox)
- Verify sufficient host memory is available
- Check if another VM is using the same resources

Network not working:
- Verify the adapter is enabled (cable connected)
- For bridged: ensure the host adapter name is correct
- For host-only: verify the host-only network is configured
- For NAT: check port forwarding rules are correct

Snapshot fails:
- Ensure sufficient disk space on the host
- Check VM is not in "aborted" state
- Verify disk is not corrupted

Template deployment fails:
- Ensure template directory exists
- Verify template metadata is valid
- Check template OVF file exists and is not corrupted

### 12.2 Performance Optimization

- Allocate no more than 50% of host RAM to VMs
- Use fixed-size disks for better IO performance
- Enable VT-x/AMD-V and nested paging
- Install Guest Additions in every VM
- Use bridged networking for production services
- Keep snapshot count under 5 per VM
- Monitor host resources before creating additional VMs

## 13. Batch Operations and Automation

### 13.1 Managing Multiple VMs Simultaneously

You can perform operations across multiple VMs efficiently. For example, to start all stopped VMs for a maintenance window, check each VM's state and start them individually based on your requirements. The system handles each VM independently, reporting success or failure per VM.

For bulk snapshot creation before a maintenance window, create snapshots on each production VM with descriptive names and timestamps. This ensures every VM has a recovery point before changes are applied.

### 13.2 Automated Workflow Patterns

Common automation patterns include:

CI/CD pipeline integration: Before deploying new software, create a snapshot of the test VM, deploy the update, run tests, and either promote the VM or roll back via snapshot restore. This pattern ensures test environments are always reproducible.

Disaster recovery testing: Schedule regular DR drills by restoring backups to isolated networks, validating application functionality, and documenting recovery time objectives. Regular testing ensures backups are valid and recovery procedures work.

Template-based provisioning: Maintain a library of golden images as templates. When a new developer joins, deploy a VM from the appropriate template with customized resources. This ensures consistent environments across the team.

## 14. Command Reference

### 14.1 VM Lifecycle Commands

- create_vm: Create a new VM with specified OS type, memory, CPU, and disk
- start_vm: Boot a VM in GUI or headless mode
- stop_vm: Power off a VM immediately
- pause_vm: Freeze VM execution
- resume_vm: Unfreeze VM execution
- save_vm: Persist VM state to disk
- reset_vm: Reboot a VM
- acpi_shutdown_vm: Graceful shutdown via ACPI
- delete_vm: Permanently remove a VM
- clone_vm: Create a full or linked clone
- modify_vm: Change VM configuration settings
- list_vms: List all VMs with optional state filter
- get_vm_info: Get detailed VM information

### 14.2 Snapshot Commands

- create_snapshot: Take a point-in-time snapshot
- restore_snapshot: Roll back to a snapshot
- list_snapshots: View snapshot tree
- delete_snapshot: Remove a snapshot

### 14.3 Network Commands

- configure_vm: Set up network adapters (NAT, bridged, host-only, internal)
- create_hostonly_network: Create a host-only network
- add_port_forwarding: Configure port forwarding rules
- list_port_forwarding: Show port forwarding rules
- get_network_info: Display VM network configuration

### 14.4 Storage Commands

- attach_disk: Connect a virtual disk to a VM
- detach_disk: Disconnect a virtual disk
- create_disk: Create a new virtual disk
- mount_iso: Attach an ISO image
- unmount_iso: Eject an ISO image
- list_storage_controllers: Show storage controller configuration

### 14.5 Template and Backup Commands

- create_template: Save VM configuration as a template
- deploy_template: Create a VM from a template
- list_templates: Show available templates
- delete_template: Remove a template
- create_backup: Backup a VM
- list_backups: Show available backups
- restore_backup: Restore VM from backup

### 14.6 Sandbox and Container Commands

- create_sandbox: Start a Docker sandbox
- run_in_sandbox: Execute a command in a sandbox
- list_sandboxes: Show active sandboxes
- stop_sandbox: Stop a running sandbox
- delete_sandbox: Remove a sandbox
- create_windows_sandbox: Create a Windows Sandbox environment
- create_portfolio_sandbox: Create sandbox from a portfolio
- run_host_file: Execute a host file in a container

### 14.7 Monitoring and Security Commands

- get_host_info: Show host system information
- get_performance_metrics: Show VM performance data
- run_health_check: Verify virtualization environment health
- run_security_scan: Scan a VM for vulnerabilities
- run_malware_analysis: Analyze VM disks for malware
- run_penetration_test: Perform security penetration testing

### 14.8 Hyper-V Commands

- list_hyperv_vms: List Hyper-V virtual machines
- get_hyperv_vm_info: Get Hyper-V VM details
- start_hyperv_vm: Start a Hyper-V VM
- stop_hyperv_vm: Stop a Hyper-V VM

## 15. Quick Start Guide for New Users

If you are new to virtualization, start with these five steps:

1. List available OS types to see what guest operating systems are supported
2. Create a small test VM with 2 GB RAM, 1 CPU, and 20 GB disk using Ubuntu_64
3. Mount a Linux ISO and start the VM in GUI mode to install the OS
4. After installation, take a snapshot called Clean Install
5. Practice starting, stopping, and modifying the VM to build familiarity

Once comfortable, explore cloning for creating test environments, snapshots for safe experimentation, templates for consistent deployments, and portmanteau tools for efficient multi-operation workflows.

For production use, always maintain a backup strategy with regular snapshots before changes, periodic full backups to external storage, and tested restore procedures. Monitor host resources to avoid over-committing memory or CPU, and use host-only or internal networks for sensitive workloads that should not be exposed to external networks.
