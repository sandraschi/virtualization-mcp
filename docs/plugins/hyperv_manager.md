# Hyper-V Manager Plugin

## Overview
The Hyper-V Manager plugin provides comprehensive management of Hyper-V virtualization environments, including virtual machines, virtual switches, and storage. It follows the FastMCP 2.10 standard for API documentation and integrates with the virtualization-mcp ecosystem.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Features](#features)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Virtual Machine Management](#virtual-machine-management)
  - [Virtual Switch Management](#virtual-switch-management)
  - [Storage Management](#storage-management)
  - [Snapshot Management](#snapshot-management)
- [WebSocket API](#websocket-api)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Best Practices](#best-practices)

## Prerequisites

- Windows 10/11 Pro, Enterprise, or Education (with Hyper-V enabled)
- Hyper-V role installed and enabled
- Administrator privileges on the host system
- PowerShell 5.1 or later
- .NET Framework 4.8 or later

## Installation

1. Ensure Hyper-V is enabled on your Windows system:
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
   ```

2. Restart your computer if prompted.

3. The plugin is enabled by default in virtualization-mcp. Verify it's running:
   ```powershell
   Get-Service virtualization-mcp | Select-Object Name, Status
   ```

## Configuration

### Plugin Configuration

```yaml
# config/plugins/hyperv_manager.yaml
enabled: true
config:
  # General settings
  host: "localhost"
  port: 8000
  use_ssl: false
  
  # VM defaults
  default_vm_path: "C:\\VMs"
  default_switch_name: "Default Switch"
  
  # Resource limits
  max_concurrent_operations: 10
  default_memory_mb: 4096
  default_vcpu_count: 2
  
  # Security
  enable_secure_boot: true
  enable_tpm: true
  
  # Logging
  log_level: "info"
  log_file: "logs/hyperv_manager.log"
  
  # Performance
  enable_live_migration: true
  enable_compression: true
  enable_smb_multichannel: true
  
  # Storage
  enable_storage_qos: true
  storage_qos_policy:
    iops_minimum: 100
    iops_maximum: 1000
    bandwidth_minimum: 10485760  # 10 MB/s
    bandwidth_maximum: 104857600  # 100 MB/s
```

### API Configuration

```yaml
# config/api.yaml
endpoints:
  hyperv:
    base_path: /api/v1/hyperv
    enabled: true
    rate_limit: "1000/hour"
    authentication: required
    cors:
      enabled: true
      allow_origins: ["*"]
      allow_methods: ["GET", "POST", "PUT", "DELETE"]
      allow_headers: ["*"]
```

## Features

### Virtual Machine Management
- Create, start, stop, and manage VMs
- Live migration between hosts
- Snapshot management
- Template-based deployment
- Resource allocation and monitoring

### Networking
- Virtual switch management
- Network isolation and VLANs
- Bandwidth management
- MAC address spoofing protection
- SR-IOV support

### Storage
- Dynamic and fixed VHD/X management
- Storage migration
- Storage QoS
- Shared VHDX for guest clustering

### Security
- Shielded VMs with BitLocker
- Virtual TPM 2.0
- Host Guardian Service integration
- Credential Guard and Device Guard

## API Documentation

### Base URL
```
/api/v1/hyperv
```

### Authentication

All API endpoints require authentication. Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Rate Limiting

- 1000 requests per hour per API key
- 100 requests per minute per IP address

### Common Headers

| Header | Description | Example |
|--------|-------------|---------|
| X-API-Key | API key for authentication | X-API-Key: abc123... |
| Accept | Response content type | Accept: application/json |
| Content-Type | Request content type | Content-Type: application/json |

### Response Format

All responses follow a standard format:

```json
{
  "status": "success",
  "data": {},
  "meta": {
    "request_id": "req_12345",
    "timestamp": "2025-08-01T22:42:33Z"
  },
  "error": null
}
```

### Error Handling

Errors follow this format:

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource": "virtual_machine",
      "id": "12345"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | Invalid request parameters |
| 401 | UNAUTHORIZED | Authentication required |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource conflict |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_SERVER_ERROR | Server error |

## Virtual Machine Management

### List VMs

```http
GET /vms
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| status | string | No | - | Filter by status (Running, Off, etc.) |
| tag | string | No | - | Filter by tag |
| limit | integer | No | 100 | Maximum number of VMs to return |
| offset | integer | No | 0 | Pagination offset |
| sort | string | No | name | Sort field (name, status, etc.) |
| order | string | No | asc | Sort order (asc/desc) |

**Response:**

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "name": "WebServer01",
        "id": "00000000-0000-0000-0000-000000000000",
        "status": "Running",
        "state": "Running",
        "uptime": "2d 4h 32m",
        "cpu_usage": 25.5,
        "memory_usage_mb": 2048,
        "memory_assigned_mb": 4096,
        "processor_count": 2,
        "ip_addresses": ["192.168.1.100"],
        "tags": ["web", "production"]
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  },
  "meta": {
    "request_id": "req_12345",
    "timestamp": "2025-08-01T22:42:33Z"
  },
  "error": null
}
```

### Create VM

```http
POST /vms
```

**Request Body:**

```json
{
  "name": "AppServer01",
  "generation": 2,
  "memory_startup_bytes": 4294967296,
  "processor_count": 4,
  "network_adapters": [
    {
      "name": "Network Adapter",
      "switch_name": "Default Switch"
    }
  ],
  "hard_drives": [
    {
      "path": "C:\\VMs\\AppServer01\\disk1.vhdx",
      "size_bytes": 107374182400
    }
  ]
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "name": "AppServer01",
    "id": "11111111-1111-1111-1111-111111111111",
    "status": "Starting",
    "console_url": "ws://localhost:8000/ws/hyperv/vms/AppServer01/console"
  },
  "meta": {
    "request_id": "req_12346",
    "timestamp": "2025-08-01T22:43:00Z"
  },
  "error": null
}
```

## Virtual Switch Management

### List Switches

```http
GET /switches
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "name": "Default Switch",
        "id": "33333333-3333-3333-3333-333333333333",
        "switch_type": "Internal",
        "net_adapter_interface_description": "Microsoft Hyper-V Network Adapter",
        "iov_enabled": true,
        "iov_queue_pairs_requested": 16,
        "iov_interrupt_moderation": "Off",
        "iov_weight": 100,
        "is_deleted": false
      }
    ],
    "total": 1
  },
  "meta": {
    "request_id": "req_12347",
    "timestamp": "2025-08-01T22:44:00Z"
  },
  "error": null
}
```

## Storage Management

### List Virtual Disks

```http
GET /storage/disks
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| path | string | No | - | Filter by path |
| type | string | No | - | Filter by type (VHD, VHDX, ISO) |
| limit | integer | No | 100 | Maximum number of disks to return |
| offset | integer | No | 0 | Pagination offset |

**Response:**

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "path": "C:\\VMs\\AppServer01\\disk1.vhdx",
        "type": "VHDX",
        "size_bytes": 107374182400,
        "file_size_bytes": 5368709120,
        "minimum_size_bytes": 10737418240,
        "logical_sector_size": 4096,
        "physical_sector_size": 4096,
        "block_size": 33554432,
        "fragmentation_percentage": 0,
        "disk_identifier": "00000000-0000-0000-0000-000000000000",
        "is_deleted": false,
        "attached_vms": ["AppServer01"]
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  },
  "meta": {
    "request_id": "req_12348",
    "timestamp": "2025-08-01T22:45:00Z"
  },
  "error": null
}
```

## Snapshot Management

### Create Snapshot

```http
POST /vms/{vm_name}/snapshots
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vm_name | string | Yes | Name of the virtual machine |

**Request Body:**

```json
{
  "name": "Before Updates",
  "description": "Snapshot before applying Windows updates"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "22222222-2222-2222-2222-222222222222",
    "name": "Before Updates",
    "vm_name": "AppServer01",
    "creation_time": "2025-08-01T22:46:00Z",
    "parent_snapshot_id": null,
    "is_current": true
  },
  "meta": {
    "request_id": "req_12349",
    "timestamp": "2025-08-01T22:46:00Z"
  },
  "error": null
}
```

## WebSocket API

The WebSocket API provides real-time updates and console access.

### Console Access

```
ws://localhost:8000/ws/hyperv/vms/{vm_name}/console
```

### Events

```
ws://localhost:8000/ws/hyperv/events
```

## Examples

### Create a New VM with PowerShell

```powershell
$body = @{
    name = "TestVM"
    generation = 2
    memory_startup_bytes = 4GB
    processor_count = 2
    network_adapters = @(
        @{
            name = "Network Adapter"
            switch_name = "Default Switch"
        }
    )
    hard_drives = @(
        @{
            path = "C:\VMs\TestVM\disk1.vhdx"
            size_bytes = 50GB
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hyperv/vms" \
    -Method Post \
    -Body $body \
    -ContentType "application/json" \
    -Headers @{ "X-API-Key" = "your-api-key-here" }
```

### Monitor VM Performance

```python
import websockets
import asyncio
import json

async def monitor_vm():
    uri = "ws://localhost:8000/ws/hyperv/events"
    async with websockets.connect(uri) as websocket:
        # Subscribe to VM performance events
        await websocket.send(json.dumps({
            "type": "subscribe",
            "event_types": ["vm_performance_update"]
        }))
        
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            if event["type"] == "vm_performance_update":
                print(f"VM: {event['data']['vm_name']}")
                print(f"CPU: {event['data']['cpu_usage']}%")
                print(f"Memory: {event['data']['memory_usage_mb']}MB")

asyncio.get_event_loop().run_until_complete(monitor_vm())
```

## Troubleshooting

### Common Issues

1. **VM Fails to Start**
   - Check Hyper-V services are running
   - Verify sufficient system resources
   - Check event logs for errors

2. **Network Connectivity Issues**
   - Verify virtual switch configuration
   - Check firewall settings
   - Ensure network adapter is properly connected

3. **Performance Problems**
   - Check host resource usage
   - Consider enabling dynamic memory
   - Verify storage performance

## Security Considerations

1. **API Security**
   - Always use HTTPS in production
   - Rotate API keys regularly
   - Implement IP whitelisting

2. **VM Security**
   - Use Shielded VMs for sensitive workloads
   - Enable TPM for encryption
   - Regularly update guest OS

## Best Practices

1. **Resource Management**
   - Use dynamic memory for better resource utilization
   - Implement resource pools for multi-tenant environments
   - Monitor and set alerts for resource usage

2. **Backup Strategy**
   - Regular VM checkpoints
   - Backup critical VMs
   - Test restore procedures

3. **Documentation**
   - Document VM configurations
   - Maintain change logs
   - Document recovery procedures

#### List All VMs
```
GET /vms
```

**Response:**
```json
{
  "vms": [
    {
      "name": "WebServer01",
      "id": "00000000-0000-0000-0000-000000000000",
      "state": "Running",
      "status": "Operating normally",
      "cpu_usage": 25,
      "memory_assigned_mb": 4096,
      "uptime_seconds": 86400
    }
  ]
}
```

#### Get VM Details
```
GET /vms/{vm_name}
```

**Parameters:**
- `vm_name` (path): Name of the virtual machine

**Response:**
```json
{
  "name": "WebServer01",
  "id": "00000000-0000-0000-0000-000000000000",
  "state": "Running",
  "status": "Operating normally",
  "cpu_usage": 25,
  "memory_assigned_mb": 4096,
  "memory_demand_mb": 3072,
  "uptime_seconds": 86400,
  "processor_count": 4,
  "memory_startup_mb": 4096,
  "dynamic_memory_enabled": true,
  "memory_minimum_mb": 1024,
  "memory_maximum_mb": 8192,
  "network_adapters": [
    {
      "name": "Network Adapter",
      "switch_name": "Default Switch",
      "mac_address": "00-15-5D-01-01-AB",
      "ip_addresses": ["192.168.1.100"],
      "status": "Connected"
    }
  ],
  "disks": [
    {
      "path": "C:\\VMs\\WebServer01\\disk1.vhdx",
      "size_gb": 100,
      "used_space_gb": 50,
      "type": "VHDX"
    }
  ],
  "checkpoints": [
    {
      "name": "Clean Install",
      "creation_time": "2023-01-01T12:00:00Z",
      "size_gb": 2.5
    }
  ]
}
```

#### Create VM
```
POST /vms
```

**Request Body:**
```json
{
  "name": "NewVM",
  "generation": 2,
  "memory_startup_bytes": 4294967296,
  "processor_count": 2,
  "dynamic_memory_enabled": true,
  "network_adapters": [
    {
      "name": "Network Adapter",
      "switch_name": "Default Switch"
    }
  ],
  "hard_drives": [
    {
      "path": "C:\\VMs\\NewVM\\disk1.vhdx",
      "size_gb": 50
    }
  ],
  "secure_boot": true,
  "tpm": true,
  "nested_virtualization": false
}
```

**Response:**
```json
{
  "status": "created",
  "vm_name": "NewVM",
  "id": "11111111-1111-1111-1111-111111111111",
  "message": "Virtual machine created successfully"
}
```

#### Start VM
```
POST /vms/{vm_name}/start
```

**Parameters:**
- `vm_name` (path): Name of the virtual machine
- `wait` (query): Wait for operation to complete (default: false)

**Response:**
```json
{
  "status": "started",
  "vm_name": "WebServer01",
  "message": "Virtual machine is starting"
}
```

#### Stop VM
```
POST /vms/{vm_name}/stop
```

**Parameters:**
- `vm_name` (path): Name of the virtual machine
- `force` (query): Force stop (default: false)
- `wait` (query): Wait for operation to complete (default: false)

**Response:**
```json
{
  "status": "stopped",
  "vm_name": "WebServer01",
  "message": "Virtual machine was stopped"
}
```

#### Create Snapshot
```
POST /vms/{vm_name}/snapshots
```

**Parameters:**
- `vm_name` (path): Name of the virtual machine

**Request Body:**
```json
{
  "name": "Before Updates",
  "description": "Snapshot before applying Windows updates"
}
```

**Response:**
```json
{
  "status": "created",
  "vm_name": "WebServer01",
  "snapshot_name": "Before Updates",
  "snapshot_id": "22222222-2222-2222-2222-222222222222",
  "message": "Snapshot created successfully"
}
```

#### List Snapshots
```
GET /vms/{vm_name}/snapshots
```

**Parameters:**
- `vm_name` (path): Name of the virtual machine

**Response:**
```json
{
  "snapshots": [
    {
      "name": "Clean Install",
      "id": "11111111-1111-1111-1111-111111111111",
      "creation_time": "2023-01-01T12:00:00Z",
      "size_gb": 2.5
    },
    {
      "name": "Before Updates",
      "id": "22222222-2222-2222-2222-222222222222",
      "creation_time": "2023-02-01T12:00:00Z",
      "size_gb": 5.1,
      "notes": "Before applying critical security updates"
    }
  ]
}
```

### Virtual Switch Management

#### List Virtual Switches
```
GET /switches
```

**Response:**
```json
{
  "switches": [
    {
      "name": "Default Switch",
      "id": "33333333-3333-3333-3333-333333333333",
      "type": "Internal",
      "connected_adapters": 3,
      "notes": "Default switch created by Hyper-V"
    },
    {
      "name": "Private Network",
      "id": "44444444-4444-4444-4444-444444444444",
      "type": "Private",
      "connected_adapters": 2,
      "notes": "Isolated network for testing"
    }
  ]
}
```

## WebSocket Events

The Hyper-V Manager plugin provides real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://your-server/ws/hyperv/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
  // Handle events like:
  // - vm_state_changed
  // - vm_performance_update
  // - snapshot_created
  // - task_completed
};
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., VM already exists)
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "error": {
    "code": "VM_NOT_FOUND",
    "message": "Virtual machine 'NonExistentVM' not found",
    "details": "No virtual machine with the specified name was found on the host."
  }
}
```

## Security Considerations

- All VM operations require authentication
- Sensitive operations (e.g., VM deletion) require confirmation
- Network operations are rate-limited to prevent abuse
- All API endpoints support HTTPS

## Performance Considerations

- Use pagination for large result sets
- Consider using WebSockets for real-time monitoring instead of polling
- Batch operations are available for bulk operations

## Examples

### Create and Start a New VM

```bash
# Create a new VM
curl -X POST http://localhost:8000/api/hyperv/vms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestVM",
    "memory_startup_bytes": 2147483648,
    "processor_count": 2,
    "network_adapters": [{"switch_name": "Default Switch"}],
    "hard_drives": [{"size_gb": 50}]
  }'

# Start the VM
curl -X POST http://localhost:8000/api/hyperv/vms/TestVM/start
```

### Take a Snapshot

```bash
curl -X POST http://localhost:8000/api/hyperv/vms/TestVM/snapshots \
  -H "Content-Type: application/json" \
  -d '{"name": "Initial State", "description": "Fresh installation"}'
```

## Integration with Other Plugins

The Hyper-V Manager plugin integrates with other virtualization-mcp plugins:

- **Security Analyzer**: Scan VMs for vulnerabilities
- **Network Analyzer**: Monitor VM network traffic
- **Malware Analyzer**: Safely analyze suspicious files in isolated VMs
- **Windows Sandbox**: Use as a lightweight alternative for quick tests



