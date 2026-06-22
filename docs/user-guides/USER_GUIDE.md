# virtualization-mcp User Guide

## Table of Contents
1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)
6. [FAQs](#faqs)

## Installation

### Prerequisites

- Python 3.8 or higher
- VirtualBox 6.0 or later
- VirtualBox Extension Pack (for advanced features)

### Installation Methods

#### Using pip (Recommended)

```bash
pip install virtualization-mcp
```

#### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/sandraschi/virtualization-mcp.git
   cd virtualization-mcp
   ```

2. Install with pip:
   ```bash
   pip install .
   ```

## Getting Started

### Starting the MCP Server

```bash
vbox-mcp --host 0.0.0.0 --port 8080
```

### Verifying the Installation

```bash
# Check version
vbox-mcp --version

# List available commands
vbox-mcp --help
```

## Basic Usage

### Listing VMs

```bash
# List all VMs
curl http://localhost:8080/api/vms

# List only running VMs
curl "http://localhost:8080/api/vms?state=running"
```

### Managing VMs

#### Start a VM

```bash
curl -X POST http://localhost:8080/api/vms/ubuntu-server/start \
  -H "Content-Type: application/json" \
  -d '{"headless": true}'
```

#### Stop a VM

```bash
curl -X POST http://localhost:8080/api/vms/ubuntu-server/stop
```

#### Create a Snapshot

```bash
curl -X POST http://localhost:8080/api/vms/ubuntu-server/snapshots \
  -H "Content-Type: application/json" \
  -d '{"name": "pre-update", "description": "Before system updates"}'
```

## Advanced Features

### Resource Monitoring

```bash
# Get VM metrics
curl http://localhost:8080/api/vms/ubuntu-server/metrics

# Get system resources
curl http://localhost:8080/api/system/resources
```

### Network Configuration

```bash
# List network adapters
curl http://localhost:8080/api/vms/ubuntu-server/network-adapters

# Configure bridged networking
curl -X PATCH http://localhost:8080/api/vms/ubuntu-server/network-adapters/0 \
  -H "Content-Type: application/json" \
  -d '{"attachment_type": "bridged", "bridge_adapter": "eth0"}'
```

### Storage Management

```bash
# List storage controllers
curl http://localhost:8080/api/vms/ubuntu-server/storage-controllers

# Attach a new disk
curl -X POST http://localhost:8080/api/vms/ubuntu-server/disks \
  -H "Content-Type: application/json" \
  -d '{"size_gb": 50, "type": "hdd", "format": "vdi"}'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VBOX_INSTALL_PATH` | Path to VirtualBox installation | Platform-dependent |
| `VBOX_USER_HOME` | Path to VirtualBox configuration | `~/.VirtualBox` |
| `VBOX_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `VBOX_API_KEY` | API key for authentication | None |

### Configuration File

Create a `config.yaml` file in the working directory:

```yaml
# virtualization-mcp configuration
server:
  host: 0.0.0.0
  port: 8080
  debug: false
  
virtualbox:
  home: ~/VirtualBox VMs
  
security:
  api_key: your-secure-api-key
  require_auth: true
  
logging:
  level: INFO
  file: virtualization-mcp.log
  max_size: 10  # MB
  backup_count: 5
```

## Troubleshooting

### Common Issues

#### VM Not Starting
- Verify VirtualBox is properly installed
- Check if VT-x/AMD-V is enabled in BIOS
- Ensure enough system resources are available

#### Network Connectivity Issues
- Verify network adapter settings
- Check firewall rules
- Ensure VirtualBox network interfaces are properly configured

#### Permission Issues
- Run VirtualBox as administrator (Windows)
- Add your user to the vboxusers group (Linux)
- Check file permissions for VM disk images

### Logs

Logs are stored in `virtualization-mcp.log` by default. Increase log level for more detailed information:

```bash
VBOX_LOG_LEVEL=DEBUG vbox-mcp
```

## FAQs

### Q: Can I run multiple instances of virtualization-mcp?
A: Yes, but each instance should use a different port and configuration.

### Q: How do I update virtualization-mcp?
```bash
pip install --upgrade virtualization-mcp
```

### Q: Is there a web interface?
A: Not currently, but you can use tools like Postman or curl to interact with the API.

### Q: How do I back up my VMs?
A: Use the snapshot feature or back up the VirtualBox VM directory.

### Q: Can I use this in production?
A: While virtualization-mcp is designed to be robust, always test thoroughly in a staging environment first.

## Support

For support, please open an issue on the [GitHub repository](https://github.com/sandraschi/virtualization-mcp/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



