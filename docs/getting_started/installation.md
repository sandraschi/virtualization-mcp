# Installation Guide

## Prerequisites

Before installing vboxmcp, ensure you have the following:

- Python 3.8 or higher
- VirtualBox 7.0 or higher (with Extension Pack recommended)
- Administrator/root privileges (for VirtualBox installation)
- Git (for source installation)

## Installation Methods

### Option 1: Install from PyPI (Recommended)

```bash
pip install vboxmcp
```

### Option 2: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/sandraschi/vboxmcp.git
   cd vboxmcp
   ```

2. Install in development mode with all dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Verifying Installation

After installation, verify that vboxmcp is installed correctly:

```bash
vboxmcp --version
```

## Configuration

vboxmcp can be configured using environment variables or a configuration file.

### Environment Variables

```bash
export VBOX_MANAGE_PATH="/usr/bin/VBoxManage"  # Path to VBoxManage
export VBOX_USER_HOME="~/.VirtualBox"           # VirtualBox configuration directory
```

### Configuration File

Create a `config.ini` file in your working directory:

```ini
[vboxmcp]
vbox_manage_path = /usr/bin/VBoxManage
vbox_user_home = ~/.VirtualBox
log_level = INFO
```

## Running the Server

### Development Mode

```bash
python -m vboxmcp.minimal_server
```

### Production Mode

For production use, it's recommended to run behind a WSGI server like Gunicorn:

```bash
gunicorn vboxmcp.minimal_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Next Steps

- [Basic Usage](../getting_started/basic_usage.md)
- [Configuration Reference](../advanced/configuration.md)
- [API Documentation](../api/)
