# Configuration Guide

This guide covers all configuration options available in the VirtualBox MCP Server.

## Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_PORT` | `8000` | Port for the MCP server to listen on |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENABLE_AUTH` | `false` | Enable API key authentication |
| `API_KEY` | (none) | API key for authentication (required if ENABLE_AUTH=true) |
| `CORS_ORIGINS` | `["*"]` | List of allowed CORS origins |

### VirtualBox Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VBOX_MANAGE_PATH` | `VBoxManage` | Path to VBoxManage executable |
| `VBOX_DEFAULT_FOLDER` | `./vms` | Default folder for VM storage |
| `VBOX_HEADLESS` | `false` | Run VMs in headless mode by default |
| `VBOX_VRDE` | `false` | Enable VRDE (Remote Desktop) by default |
| `VBOX_VRDE_PORT` | `3390` | Starting port for VRDE connections |

### Performance Tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_COUNT` | CPU count | Number of worker processes |
| `MAX_CONCURRENT_OPS` | `5` | Maximum concurrent operations |
| `OPERATION_TIMEOUT` | `300` | Default operation timeout in seconds |
| `CACHE_TTL` | `300` | Cache time-to-live in seconds |

## Configuration Files

### config.toml

Create a `config.toml` file in the working directory:

```toml
[server]
port = 8000
log_level = "INFO"

[auth]
enabled = true
api_key = "your-secure-key"

[virtualbox]
vboxmanage_path = "/usr/bin/VBoxManage"
default_folder = "/path/to/vms"
headless = false

[performance]
worker_count = 4
max_concurrent_ops = 5
operation_timeout = 300
```

### VM Templates

Define custom VM templates in `templates.toml`:

```toml
[ubuntu-2204]
description = "Ubuntu 22.04 LTS"
os_type = "Ubuntu_64"
memory_mb = 4096
disk_gb = 20
cpus = 2
network = "nat"

[windows-11]
description = "Windows 11"
os_type = "Windows11_64"
memory_mb = 8192
disk_gb = 60
cpus = 4
network = "nat"
```

## Network Configuration

### Port Forwarding

Configure port forwarding in `network.toml`:

```toml
[forwarding.ubuntu-dev]
vm_name = "ubuntu-dev"
guest_port = 80
host_port = 8080
protocol = "tcp"

[forwarding.web-server]
vm_name = "web-server"
guest_port = 22
host_port = 2222
protocol = "tcp"
```

### Network Modes

Supported network modes:
- `nat`: Network Address Translation (default)
- `natnetwork`: NAT Network
- `bridged`: Bridged Networking
- `intnet`: Internal Network
- `hostonly`: Host-only Networking

## Security Configuration

### SSL/TLS

Enable HTTPS by setting these environment variables:

```bash
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem
```

### Authentication

Enable and configure authentication:

```bash
# Enable authentication
ENABLE_AUTH=true

# Set a secure API key
API_KEY="your-secure-api-key"

# Optional: Require authentication for all endpoints
AUTH_REQUIRED=true
```

## Logging Configuration

### Log Levels
- `DEBUG`: Detailed debug information
- `INFO`: General operational information
- `WARNING`: Indications of potential issues
- `ERROR`: Errors that don't prevent the server from running
- `CRITICAL`: Critical errors that prevent normal operation

### Log Rotation

Configure log rotation in `logging.toml`:

```toml
[handlers.file]
class = "logging.handlers.RotatingFileHandler"
filename = "vboxmcp.log"
maxBytes = 10485760  # 10MB
backupCount = 5
encoding = "utf8"

[formatters.default]
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

[loggers]
"" = {level = "INFO", handlers = ["console", "file"]}
"vboxmcp" = {level = "DEBUG", handlers = ["file"], propagate = false}
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
LOG_LEVEL=DEBUG
VBOX_HEADLESS=false
```

### Production

```bash
# .env.production
LOG_LEVEL=WARNING
ENABLE_AUTH=true
VBOX_HEADLESS=true
```

## Configuration Precedence

1. Command-line arguments
2. Environment variables
3. `.env` file
4. `config.toml`
5. Default values

## Verifying Configuration

Check the current configuration:

```bash
curl http://localhost:8000/api/config
```

This will return the current configuration with sources.
