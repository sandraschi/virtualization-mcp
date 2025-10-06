# vboxmcp MCP Client Guide

Welcome to the vboxmcp MCP Client Guide! This document explains how to use vboxmcp tools within MCP clients like Claude, using natural language interactions.

## Table of Contents
- [Introduction to vboxmcp Tools](#introduction-to-vboxmcp-tools)
- [Basic Usage](#basic-usage)
- [Virtual Machine Management](#virtual-machine-management)
- [Storage Management](#storage-management)
- [Networking](#networking)
- [Security Tools](#security-tools)
- [Monitoring](#monitoring)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Introduction to vboxmcp Tools

vboxmcp provides a comprehensive set of tools for managing virtual machines, storage, networking, and security. These tools are available in MCP clients like Claude, allowing you to perform complex VM operations using natural language.

### Key Features
- **Virtual Machine Lifecycle**: Create, start, stop, and manage VMs
- **Storage Management**: Handle disks, ISOs, and storage controllers
- **Networking**: Configure virtual networks and adapters
- **Security**: Scan for vulnerabilities and analyze potential threats
- **Monitoring**: Track system resources and VM performance
- **Documentation**: Maintain system documentation

## Basic Usage

### Starting a VM
To start a virtual machine, simply ask Claude to start it by name:

> "Start the Windows 10 VM"
> "Power on the Ubuntu server"

### Checking VM Status
Get the current status of your VMs:

> "List all running VMs"
> "Is my Windows VM running?"
> "Show me the status of the Ubuntu server"

## Virtual Machine Management

### Creating a New VM
Create a new virtual machine with specific settings:

> "Create a new Ubuntu 22.04 VM with 4GB RAM and 2 CPUs"
> "Set up a Windows 11 VM with 8GB RAM and 100GB disk"

### Managing VM State
Control your VMs with simple commands:

> "Pause the Windows VM"
> "Resume the Ubuntu VM"
> "Reset the test VM"
> "Shut down all VMs"

### Snapshots
Work with VM snapshots:

> "Create a snapshot of the Windows VM called 'before_update'"
> "List all snapshots for the Ubuntu VM"
> "Restore the Ubuntu VM to the 'clean_install' snapshot"
> "Delete the 'test_snapshot' from the Windows VM"

## Storage Management

### Managing Virtual Disks
Handle virtual disks with ease:

> "Create a new 50GB disk for the database VM"
> "Attach the data_disk.vdi to the Windows VM"
> "Resize the Ubuntu disk to 200GB"

### Working with ISOs
Mount and unmount ISO images:

> "Mount Ubuntu-22.04.iso to the VM's DVD drive"
> "Unmount the ISO from the Windows VM"
> "List all mounted ISOs"

## Networking

### Network Configuration
Manage VM networking:

> "Show network adapters for the Windows VM"
> "Connect the Ubuntu VM to the NAT network"
> "Set up port forwarding for RDP on port 3389"

### Network Analysis
Use the network analyzer tools:

> "Scan for open ports on the Ubuntu VM"
> "List active network connections"
> "Show network interface statistics"

## Security Tools

### Malware Analysis
Analyze files for potential threats:

> "Scan the 'downloads' folder for malware"
> "Analyze suspicious_file.exe in the sandbox"
> "Check the last malware scan results"

### Security Scanning
Scan your VMs for vulnerabilities:

> "Run a security scan on the Windows VM"
> "Check for outdated software on the Ubuntu server"
> "Show me the last security report"

## Monitoring

### System Metrics
Monitor system resources:

> "Show CPU and memory usage"
> "Display disk space on all VMs"
> "What's the network bandwidth usage?"

### Alerts
Set up and manage alerts:

> "Alert me if CPU usage goes above 90%"
> "List all active alerts"
> "Mute alerts for the next hour"

## Documentation

### Managing Documentation
Work with system documentation:

> "Create a new documentation page about the network setup"
> "Show me the documentation for the backup process"
> "Update the Windows setup guide with the new steps"

### Exporting Documentation
Export documentation for sharing:

> "Export the network documentation as HTML"
> "Save the VM setup guide as a PDF"

## Troubleshooting

### Common Issues

#### VM Won't Start
> "The Windows VM won't start. What should I check?"
> "Ubuntu VM is stuck at boot. Help me troubleshoot."

#### Network Problems
> "The VM can't connect to the internet. What's wrong?"
> "I can't ping between VMs. How do I fix this?"

#### Performance Issues
> "The VM is running slowly. How can I improve performance?"
> "How do I allocate more resources to a VM?"

## Examples

### Example Workflows

#### Setting Up a Development Environment
> "Create a new Ubuntu 22.04 VM with 4GB RAM and 2 CPUs"
> "Install Docker on the Ubuntu VM"
> "Set up port forwarding for port 8080"
> "Take a snapshot called 'docker_installed'"

#### Creating a Test Environment
> "Clone the production VM to create a test environment"
> "Create a snapshot called 'before_changes'"
> "Apply the software update"
> "Test the application"
> "Revert to the 'before_changes' snapshot if tests fail"

#### Monitoring System Health
> "Show me the current system resources"
> "Alert me if disk space is below 10%"
> "Generate a weekly report of VM performance"

## Getting Help

For additional help with vboxmcp tools:

> "Show me all available commands"
> "How do I back up a VM?"
> "What's the best way to optimize VM performance?"

Remember, you can always ask Claude for help with any vboxmcp task using natural language. The system will handle the complex commands for you!
