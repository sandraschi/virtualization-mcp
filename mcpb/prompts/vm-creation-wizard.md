# VM Creation Wizard Prompt

## Purpose
Guide users through creating virtual machines with optimal configurations for their specific use case.

## Workflow

### Step 1: Determine Use Case
Ask the user:
- What will this VM be used for? (development, testing, server, desktop, etc.)
- What operating system do you want to install?
- Do you have specific performance requirements?

### Step 2: Recommend Configuration
Based on use case, recommend:

#### For Development (Desktop Linux/Windows)
- **Memory**: 4-8 GB
- **CPUs**: 2-4 cores
- **Disk**: 40-60 GB
- **Network**: NAT + Host-Only (for SSH access)
- **Video**: 128 MB VRAM, 3D acceleration enabled

#### For Testing/Sandbox
- **Memory**: 2-4 GB
- **CPUs**: 1-2 cores
- **Disk**: 20-40 GB
- **Network**: Internal network (isolated)
- **Snapshot**: Enable snapshot before each test

#### For Server (Headless)
- **Memory**: 2-16 GB (depending on services)
- **CPUs**: 2-4 cores
- **Disk**: 20-100 GB (depending on data)
- **Network**: Bridged or NAT with port forwarding
- **Mode**: Headless startup

#### For Desktop Use
- **Memory**: 4-8 GB
- **CPUs**: 2-4 cores
- **Disk**: 60-100 GB
- **Network**: NAT (simple internet access)
- **Video**: 256 MB VRAM, 3D acceleration enabled
- **Mode**: GUI startup

### Step 3: Create VM
Execute creation with recommended settings, allowing user to customize.

### Step 4: Post-Creation Tasks
Guide user through:
1. Mounting OS installation ISO
2. Starting VM in appropriate mode
3. Installing operating system
4. Installing Guest Additions
5. Creating "Clean Install" snapshot
6. Configuring network as needed

## Example Interaction

**User**: "I need a VM for web development"

**Assistant**: 
"I'll help you set up a web development VM. I recommend:

**Configuration**:
- Ubuntu 22.04 Desktop (developer-friendly)
- 4 GB RAM (sufficient for IDE + browser + dev tools)
- 2 CPUs (good performance for development tasks)
- 60 GB disk (OS + dev tools + projects)
- NAT network (for internet access)
- Port forwarding: 3000→3000, 8080→8080 (common dev ports)

Would you like to proceed with this configuration, or would you like to adjust anything?"

**After confirmation**: Create the VM, then guide through:
1. Mounting Ubuntu ISO
2. Starting in GUI mode
3. Installing Ubuntu
4. Setting up Guest Additions
5. Configuring port forwarding
6. Taking snapshot after setup

