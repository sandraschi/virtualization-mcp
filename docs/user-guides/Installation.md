# Installation Guide

This guide will help you install and set up the VirtualBox MCP Server.

## Prerequisites

- Python 3.8 or higher
- VirtualBox 7.0 or higher
- Administrative privileges (for VirtualBox installation)

## Installation Methods

### Method 1: Using pip (Recommended)

```bash
# Install the package
pip install virtualization-mcp

# Verify installation
virtualization-mcp --version
```

### Method 2: From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/virtualization-mcp.git
cd virtualization-mcp

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Method 3: Using Docker

```bash
# Pull the Docker image
docker pull yourusername/virtualization-mcp:latest

# Run the container
docker run -d --name virtualization-mcp \
  -v /var/run/vboxms:/var/run/vboxms \
  -v /path/to/vms:/vms \
  -p 8000:8000 \
  yourusername/virtualization-mcp
```

## Configuration

1. Create a `.env` file in the project root:

```env
# VirtualBox Configuration
VBOX_MANAGE_PATH=/usr/bin/VBoxManage
VBOX_DEFAULT_FOLDER=/path/to/vms

# Server Configuration  
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO

# Security
ENABLE_AUTH=true
API_KEY=your_secure_api_key
```

2. Configure VirtualBox permissions:

```bash
# Add your user to the vboxusers group
sudo usermod -aG vboxusers $USER

# Verify VirtualBox installation
VBoxManage --version
```

## Verifying the Installation

1. Start the MCP server:
   ```bash
   virtualization-mcp start
   ```

2. In a new terminal, test the API:
   ```bash
   curl http://localhost:8000/api/version
   ```

3. Access the web interface at `http://localhost:8000`

## Troubleshooting

### Common Issues

1. **VirtualBox not found**
   - Verify VirtualBox is installed
   - Check the `VBOX_MANAGE_PATH` in your `.env` file

2. **Permission denied**
   - Ensure your user is in the `vboxusers` group
   - Restart your session after adding to the group

3. **Port already in use**
   - Change the `MCP_SERVER_PORT` in `.env`
   - Check for other services using the port

For additional help, please refer to the [Troubleshooting](Troubleshooting) guide.



