# Windows Sandbox Plugin

## Overview

The Windows Sandbox plugin provides a lightweight, disposable desktop environment for safely running untrusted applications. It leverages Windows 10/11's built-in Windows Sandbox feature to create isolated, temporary environments that are discarded after use.

## Features

- **Lightweight**: Uses native Windows Sandbox for minimal overhead
- **Disposable**: All changes are discarded when closed
- **Secure**: Runs in an isolated environment
- **Configurable**: Customize CPU, memory, and storage
- **File Sharing**: Share folders between host and sandbox
- **Networking**: Configurable network access
- **Clipboard Integration**: Share clipboard between host and sandbox
- **Printer Redirection**: Access host printers from the sandbox
- **Audio Support**: Play audio from applications in the sandbox
- **GPU Acceleration**: Optional GPU acceleration for better performance

## Prerequisites

- Windows 10 Pro/Enterprise/Education (version 1903 or later)
- Virtualization enabled in BIOS/UEFI
- Windows Sandbox feature enabled
- At least 4GB of RAM (8GB recommended)
- At least 1GB of free disk space

## Installation

1. Ensure Windows Sandbox is enabled:
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -All -NoRestart
   ```

2. Restart your computer if prompted.

3. The plugin is enabled by default in virtualization-mcp. Verify it's running:
   ```powershell
   Get-Service virtualization-mcp | Select-Object Name, Status
   ```

## Configuration

### Plugin Configuration

```yaml
# config/plugins/windows_sandbox.yaml
enabled: true
config:
  # Sandbox configuration
  memory_mb: 4096
  vcpu_count: 2
  gpu_enabled: true
  network_enabled: true
  audio_input_enabled: false
  video_input_enabled: false
  protected_client: true
  printer_redirection: false
  clipboard_redirection: true
  
  # Default shared folders (read-only by default)
  shared_folders:
    - host_path: C:\\shared
      read_only: true
      
  # Logging
  log_level: "info"
  log_file: "logs/windows_sandbox.log"
  
  # Timeout in seconds (0 for no timeout)
  idle_timeout: 0
  
  # Automatic cleanup of temporary files (in hours)
  cleanup_after_hours: 24
```

### API Configuration

```yaml
# config/api.yaml
endpoints:
  windows_sandbox:
    base_path: /api/v1/sandbox
    enabled: true
    rate_limit: "100/hour"
    authentication: required
```

## API Reference

### Base URL

```
/api/v1/sandbox
```

### Endpoints

#### Create a Sandbox

```http
POST /sandboxes
```

**Request Body:**

```json
{
  "name": "test-sandbox",
  "config": {
    "memory_mb": 4096,
    "vcpu_count": 2,
    "gpu_enabled": true,
    "shared_folders": [
      {
        "host_path": "C:\\projects",
        "read_only": false
      }
    ]
  }
}
```

**Response:**

```json
{
  "id": "sandbox-12345",
  "name": "test-sandbox",
  "status": "running",
  "ip_address": "172.16.0.2",
  "console_url": "ws://localhost:8000/ws/sandbox/sandbox-12345/console",
  "created_at": "2025-08-01T22:42:33Z",
  "expires_at": "2025-08-02T22:42:33Z"
}
```

#### List Sandboxes

```http
GET /sandboxes
```

**Query Parameters:**

| Parameter | Type    | Description                |
|-----------|---------|----------------------------|
| status    | string  | Filter by status           |
| limit     | integer | Max number of sandboxes    |
| offset    | integer | Pagination offset          |

**Response:**

```json
{
  "items": [
    {
      "id": "sandbox-12345",
      "name": "test-sandbox",
      "status": "running",
      "ip_address": "172.16.0.2",
      "created_at": "2025-08-01T22:42:33Z",
      "expires_at": "2025-08-02T22:42:33Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Sandbox Status

```http
GET /sandboxes/{sandbox_id}
```

**Response:**

```json
{
  "id": "sandbox-12345",
  "name": "test-sandbox",
  "status": "running",
  "ip_address": "172.16.0.2",
  "cpu_usage": 25.5,
  "memory_usage": 2048,
  "disk_usage": 1024,
  "network_in": 524288,
  "network_out": 262144,
  "processes": 42,
  "uptime_seconds": 3600,
  "created_at": "2025-08-01T22:42:33Z",
  "expires_at": "2025-08-02T22:42:33Z"
}
```

#### Execute Command in Sandbox

```http
POST /sandboxes/{sandbox_id}/execute
```

**Request Body:**

```json
{
  "command": "ipconfig /all",
  "timeout_seconds": 30,
  "working_directory": "C:\\",
  "environment": {
    "PATH": "C:\\Windows\\System32"
  }
}
```

**Response:**

```json
{
  "exit_code": 0,
  "stdout": "Windows IP Configuration\r\n   Host Name . . . . . . . . . . . . : WIN-SANDBOX-1\r\n   Primary Dns Suffix  . . . . . . . : \r\n   Node Type . . . . . . . . . . . . : Hybrid\r\n   IP Routing Enabled. . . . . . . . : No\r\n   WINS Proxy Enabled. . . . . . . . : No\r\n   DNS Suffix Search List. . . . . . : example.com\r\n\r\nEthernet adapter Ethernet:\r\n\r\n   Connection-specific DNS Suffix  . : example.com\r\n   Description . . . . . . . . . . . : Microsoft Hyper-V Network Adapter\r\n   Physical Address. . . . . . . . . : 00-15-5D-01-02-03\r\n   DHCP Enabled. . . . . . . . . . . : Yes\r\n   Autoconfiguration Enabled . . . . : Yes\r\n   Link-local IPv6 Address . . . . . : fe80::a123:b456:c789:d012%4(Preferred) \r\n   IPv4 Address. . . . . . . . . . . : 172.16.0.2(Preferred) \r\n   Subnet Mask . . . . . . . . . . . : 255.240.0.0\r\n   Lease Obtained. . . . . . . . . . : Wednesday, July 31, 2025 10:00:00 AM\r\n   Lease Expires . . . . . . . . . . : Thursday, August 1, 2025 10:00:00 AM\r\n   Default Gateway . . . . . . . . . : 172.16.0.1\r\n   DHCP Server . . . . . . . . . . . : 172.16.0.1\r\n   DHCPv6 IAID . . . . . . . . . . . : 50331648\r\n   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-2A-5E-4C-3D-00-15-5D-01-02-03\r\n   DNS Servers . . . . . . . . . . . : 8.8.8.8\r\n   NetBIOS over Tcpip. . . . . . . . : Enabled\r\n",
  "stderr": "",
  "execution_time_ms": 125,
  "timed_out": false
}
```

#### Upload File to Sandbox

```http
POST /sandboxes/{sandbox_id}/files
Content-Type: multipart/form-data
```

**Form Data:**

| Field        | Type   | Description                     |
|--------------|--------|---------------------------------|
| file         | file   | File to upload                  |
| destination  | string | Destination path in sandbox     |
| mode         | string | File mode (e.g., '0755')        |
| owner        | string | File owner (e.g., 'SYSTEM')     |

**Response:**

```json
{
  "path": "C:\\Users\\WDAGUtilityAccount\\Desktop\\test.txt",
  "size": 1024,
  "checksum": "a1b2c3d4e5f6...",
  "created_at": "2025-08-01T22:45:00Z"
}
```

#### Download File from Sandbox

```http
GET /sandboxes/{sandbox_id}/files
```

**Query Parameters:**

| Parameter | Type   | Description                |
|-----------|--------|----------------------------|
| path      | string | Path to file in sandbox    |

**Response:**

The file contents as an attachment.

#### Connect to Sandbox Console

```http
GET /sandboxes/{sandbox_id}/console
Upgrade: websocket
Connection: Upgrade
```

Establishes a WebSocket connection to the sandbox console.

#### Take Screenshot

```http
GET /sandboxes/{sandbox_id}/screenshot
```

**Query Parameters:**

| Parameter | Type    | Description                |
|-----------|---------|----------------------------|
| width     | integer | Width in pixels (optional) |
| height    | integer | Height in pixels (optional)|

**Response:**

PNG image data.

#### Terminate Sandbox

```http
DELETE /sandboxes/{sandbox_id}
```

**Query Parameters:**

| Parameter | Type    | Description                |
|-----------|---------|----------------------------|
| force     | boolean | Force termination          |

**Response:**

```json
{
  "status": "terminated",
  "id": "sandbox-12345",
  "message": "Sandbox terminated successfully"
}
```

## WebSocket API

The WebSocket API allows real-time interaction with sandbox consoles.

### Connection URL

```
ws://localhost:8000/ws/sandbox/{sandbox_id}/console
```

### Message Types

#### Terminal Data

```json
{
  "type": "stdout",
  "data": "Hello, World!\r\n",
  "timestamp": "2025-08-01T22:50:00Z"
}
```

#### Terminal Resize

```json
{
  "type": "resize",
  "width": 80,
  "height": 24
}
```

#### Terminal Input

```json
{
  "type": "stdin",
  "data": "ipconfig\r"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": {
    "code": "INVALID_CONFIGURATION",
    "message": "Invalid sandbox configuration",
    "details": {
      "memory_mb": "Value must be between 1024 and 8192"
    }
  }
}
```

### 404 Not Found

```json
{
  "error": {
    "code": "SANDBOX_NOT_FOUND",
    "message": "Sandbox not found",
    "details": {
      "sandbox_id": "nonexistent-id"
    }
  }
}
```

### 409 Conflict

```json
{
  "error": {
    "code": "SANDBOX_ALREADY_EXISTS",
    "message": "A sandbox with this name already exists",
    "details": {
      "name": "duplicate-name"
    }
  }
}
```

## Security Considerations

1. **Isolation**: Each sandbox runs in an isolated environment
2. **Resource Limits**: CPU, memory, and disk usage are limited
3. **Network Restrictions**: Outbound traffic can be restricted
4. **Temporary Storage**: All changes are discarded when the sandbox is closed
5. **Access Control**: API access requires authentication

## Troubleshooting

### Common Issues

1. **Sandbox fails to start**:
   - Verify Windows Sandbox is enabled in Windows Features
   - Check the Hyper-V role is installed
   - Ensure virtualization is enabled in BIOS/UEFI

2. **Network connectivity issues**:
   - Verify the host firewall allows Windows Sandbox traffic
   - Check network adapter settings in the sandbox configuration

3. **Performance problems**:
   - Allocate more CPU cores and memory if available
   - Enable GPU acceleration if supported
   - Close unnecessary applications on the host

### Logs

Logs are available at:
- `%PROGRAMDATA%\\virtualization-mcp\\logs\\windows_sandbox.log`
- Event Viewer: `Applications and Services Logs > virtualization-mcp`

## Examples

### Start a Sandbox with a Shared Folder

```bash
curl -X POST http://localhost:8000/api/v1/sandbox/sandboxes \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "dev-environment",
    "config": {
      "memory_mb": 4096,
      "vcpu_count": 2,
      "shared_folders": [
        {
          "host_path": "C:\\projects",
          "read_only": false
        }
      ]
    }
  }'
```

### Run a Command in the Sandbox

```bash
curl -X POST http://localhost:8000/api/v1/sandbox/sandboxes/sandbox-12345/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"command": "systeminfo"}'
```

### Connect to the Sandbox Console

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/sandbox/sandbox-12345/console');

ws.onopen = () => {
  console.log('Connected to sandbox console');
  // Send a command
  ws.send(JSON.stringify({
    type: 'stdin',
    data: 'ipconfig\r'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'stdout') {
    console.log('Output:', message.data);
  } else if (message.type === 'stderr') {
    console.error('Error:', message.data);
  }
};

ws.onclose = () => {
  console.log('Disconnected from sandbox console');
};
```

## Best Practices

1. **Resource Management**:
   - Set appropriate memory and CPU limits
   - Monitor resource usage
   - Terminate unused sandboxes

2. **Security**:
   - Use read-only shared folders when possible
   - Restrict network access
   - Regularly update the host system

3. **Performance**:
   - Enable GPU acceleration for graphical applications
   - Allocate sufficient memory for your workload
   - Use SSD storage for better I/O performance

4. **Development Workflow**:
   - Use version control for sandbox configurations
   - Document your sandbox environments
   - Automate common tasks with the API

## License

This plugin is part of virtualization-mcp and is licensed under the [MIT License](https://opensource.org/licenses/MIT).



