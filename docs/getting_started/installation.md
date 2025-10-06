# Installation Guide

## Prerequisites

Before installing virtualization-mcp, ensure you have the following:

- Python 3.8 or higher
- VirtualBox 7.0 or higher (with Extension Pack recommended)
- Administrator/root privileges (for VirtualBox installation)
- Git (for source installation)

## Installation Methods

### Option 1: Install from PyPI (Recommended)

```bash
pip install virtualization-mcp
```

### Option 2: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/sandraschi/virtualization-mcp.git
   cd virtualization-mcp
   ```

2. Install in development mode with all dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Verifying Installation

After installation, verify that virtualization-mcp is installed correctly:

```bash
virtualization-mcp --version
```

## Configuration

virtualization-mcp can be configured using environment variables or a configuration file.

### Environment Variables

```bash
export VBOX_MANAGE_PATH="/usr/bin/VBoxManage"  # Path to VBoxManage
export VBOX_USER_HOME="~/.VirtualBox"           # VirtualBox configuration directory
```

### Configuration File

Create a `config.ini` file in your working directory:

```ini
[virtualization-mcp]
vbox_manage_path = /usr/bin/VBoxManage
vbox_user_home = ~/.VirtualBox
log_level = INFO
```

## Running the Server

### Development Mode

```bash
python -m virtualization-mcp.minimal_server
```

### Production Mode

For production use, it's recommended to run behind a WSGI server like Gunicorn:

```bash
gunicorn virtualization-mcp.minimal_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Next Steps

- [Basic Usage](../getting_started/basic_usage.md)
- [Configuration Reference](../advanced/configuration.md)
- [API Documentation](../api/)



