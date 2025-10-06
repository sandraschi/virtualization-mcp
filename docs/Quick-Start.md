# Quick Start Guide

This guide will help you quickly get started with the VirtualBox MCP Server.

## Prerequisites

- VirtualBox MCP Server installed (see [Installation](Installation))
- VirtualBox 7.0 or higher installed
- Basic familiarity with command line interfaces

## Starting the Server

1. **Start the MCP Server**:
   ```bash
   vboxmcp start
   ```
   This will start the server on `http://localhost:8000` by default.

2. **Verify the server is running**:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return: `{"status":"ok"}`

## Basic VM Management

### Create a New VM

```bash
# Create a new Ubuntu VM with 4GB RAM and 20GB disk
curl -X POST http://localhost:8000/api/vms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ubuntu-dev",
    "template": "ubuntu-2204",
    "memory_mb": 4096,
    "disk_gb": 20
  }'
```

### List All VMs

```bash
curl http://localhost:8000/api/vms
```

### Start a VM

```bash
curl -X POST http://localhost:8000/api/vms/ubuntu-dev/start
```

### Create a Snapshot

```bash
curl -X POST http://localhost:8000/api/vms/ubuntu-dev/snapshots \
  -H "Content-Type: application/json" \
  -d '{"name": "clean-state"}'
```

## Windows Sandbox Quick Start

### Create a Windows Sandbox

```bash
# Create a Windows Sandbox with 4GB RAM
curl -X POST http://localhost:8000/api/sandbox \
  -H "Content-Type: application/json" \
  -d '{
    "name": "win11-sandbox",
    "memory_mb": 4096,
    "iso_path": "path/to/windows11.iso"
  }'
```

### List Sandboxes

```bash
curl http://localhost:8000/api/sandbox
```

## Product Key Management

### Store a Product Key

```bash
curl -X POST http://localhost:8000/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "key": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
    "os_version": "Windows 11 Pro",
    "purpose": "development"
  }'
```

### List Stored Keys

```bash
curl http://localhost:8000/api/keys
```

## Next Steps

- Explore the [API Reference](API-Reference) for all available endpoints
- Learn about [Advanced Configuration](Configuration)
- Check out [Common Use Cases](Use-Cases) for practical examples
- Visit the [FAQ](FAQ) for troubleshooting help

## Getting Help

If you encounter any issues:
1. Check the [Troubleshooting](Troubleshooting) guide
2. Search the [GitHub Issues](https://github.com/yourusername/vboxmcp/issues)
3. [Open a new issue](https://github.com/yourusername/vboxmcp/issues/new) if your problem isn't listed
