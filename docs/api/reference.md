# API Reference

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Endpoints](#endpoints)
   - [VM Management](#vm-management)
   - [Snapshot Management](#snapshot-management)
   - [Storage Management](#storage-management)
   - [Network Management](#network-management)
   - [System Operations](#system-operations)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [WebSocket API](#websocket-api)
7. [Examples](#examples)

## Authentication

All API requests require authentication using API keys. Include your API key in the `X-API-Key` header.

```http
GET /api/v1/vms HTTP/1.1
Host: api.vboxmcp.example.com
X-API-Key: your-api-key-here
```

## Base URL

The base URL for all API endpoints is:

```
https://api.vboxmcp.example.com/api/v1
```

For local development:

```
http://localhost:8000/api/v1
```

## Endpoints

### VM Management

#### List All VMs

```http
GET /vms
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "vm-123456",
      "name": "ubuntu-server",
      "state": "running",
      "os_type": "Ubuntu_64",
      "memory_mb": 4096,
      "cpus": 2,
      "uptime_seconds": 12345
    }
  ]
}
```

#### Get VM Details

```http
GET /vms/{vm_id_or_name}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "vm-123456",
    "name": "ubuntu-server",
    "state": "running",
    "os_type": "Ubuntu_64",
    "memory_mb": 4096,
    "cpus": 2,
    "uptime_seconds": 12345,
    "storage_controllers": [
      {
        "name": "SATA Controller",
        "type": "sata",
        "port_count": 4,
        "attachments": [
          {
            "port": 0,
            "device": 0,
            "type": "hdd",
            "medium": "/path/to/disk.vdi",
            "size_gb": 50,
            "used_gb": 25
          }
        ]
      }
    ],
    "network_adapters": [
      {
        "slot": 0,
        "enabled": true,
        "type": "82540EM",
        "mac_address": "080027123456",
        "cable_connected": true,
        "speed_mbps": 1000,
        "mode": "nat"
      }
    ]
  }
}
```

#### Create VM

```http
POST /vms
```

**Request Body:**

```json
{
  "name": "new-vm",
  "os_type": "Ubuntu_64",
  "memory_mb": 4096,
  "cpus": 2,
  "storage_gb": 50,
  "network": {
    "adapter1": {
      "enabled": true,
      "type": "nat",
      "adapter_type": "82540EM"
    }
  },
  "storage_controllers": [
    {
      "name": "SATA Controller",
      "type": "sata",
      "port_count": 4
    }
  ]
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "vm-789012",
    "name": "new-vm",
    "state": "poweroff",
    "message": "VM created successfully"
  }
}
```

#### Start VM

```http
POST /vms/{vm_id_or_name}/start
```

**Request Body (optional):**

```json
{
  "headless": true,
  "gui": false
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "vm-123456",
    "name": "ubuntu-server",
    "state": "starting",
    "message": "VM is starting"
  }
}
```

### Snapshot Management

#### Create Snapshot

```http
POST /vms/{vm_id_or_name}/snapshots
```

**Request Body:**

```json
{
  "name": "pre-update",
  "description": "State before system update",
  "include_ram": false
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "snapshot_id": "snap-123456",
    "name": "pre-update",
    "timestamp": "2023-01-01T12:00:00Z",
    "online": false
  }
}
```

#### Restore Snapshot

```http
POST /vms/{vm_id_or_name}/snapshots/{snapshot_id}/restore
```

**Request Body (optional):**

```json
{
  "start_vm": true
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "vm_id": "vm-123456",
    "snapshot_id": "snap-123456",
    "previous_state": "running",
    "message": "Snapshot restored successfully"
  }
}
```

### Storage Management

#### List Disks

```http
GET /vms/{vm_id_or_name}/disks
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "controller": "SATA Controller",
      "port": 0,
      "device": 0,
      "type": "hdd",
      "medium": "/path/to/disk.vdi",
      "size_gb": 50,
      "used_gb": 25,
      "format": "vdi"
    }
  ]
}
```

#### Attach Disk

```http
POST /vms/{vm_id_or_name}/disks
```

**Request Body:**

```json
{
  "controller": "SATA Controller",
  "port": 1,
  "device": 0,
  "type": "hdd",
  "medium": "/path/to/new-disk.vdi",
  "create_if_missing": true,
  "size_gb": 100
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "controller": "SATA Controller",
    "port": 1,
    "device": 0,
    "message": "Disk attached successfully"
  }
}
```

### Network Management

#### List Network Adapters

```http
GET /vms/{vm_id_or_name}/network-adapters
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "slot": 0,
      "enabled": true,
      "type": "82540EM",
      "mac_address": "080027123456",
      "cable_connected": true,
      "speed_mbps": 1000,
      "mode": "nat"
    }
  ]
}
```

#### Configure Network Adapter

```http
PUT /vms/{vm_id_or_name}/network-adapters/{slot}
```

**Request Body:**

```json
{
  "enabled": true,
  "type": "82540EM",
  "cable_connected": true,
  "mode": "bridged",
  "bridge_adapter": "eth0"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "slot": 0,
    "message": "Network adapter updated"
  }
}
```

### System Operations

#### Get System Info

```http
GET /system/info
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "version": "1.0.0",
    "api_version": "1.0",
    "host": {
      "os": "Linux",
      "cpus": 8,
      "memory_mb": 32768,
      "virtualbox_version": "7.0.0"
    },
    "limits": {
      "max_vms": 100,
      "max_memory_per_vm": 65536,
      "max_cpus_per_vm": 32
    }
  }
}
```

## Error Handling

All error responses follow this format:

```json
{
  "status": "error",
  "error": {
    "code": "vm_not_found",
    "message": "The specified VM was not found",
    "details": {
      "vm_id": "vm-999999"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `invalid_request` | The request was malformed |
| `unauthorized` | Invalid or missing API key |
| `forbidden` | Insufficient permissions |
| `not_found` | The requested resource was not found |
| `vm_not_running` | The VM is not running |
| `vm_already_running` | The VM is already running |
| `insufficient_resources` | Not enough system resources available |
| `invalid_state` | The operation is not allowed in the current state |
| `operation_failed` | The operation failed |

## Rate Limiting

API requests are rate limited to prevent abuse. The following headers are included in all responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed per time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current window
- `X-RateLimit-Reset`: The time at which the current window resets (UTC epoch seconds)

## WebSocket API

For real-time events and console access, use the WebSocket API:

```
wss://api.vboxmcp.example.com/api/v1/ws
```

### Authentication

Send an authentication message after connecting:

```json
{
  "type": "auth",
  "api_key": "your-api-key-here"
}
```

### Console Access

To access the VM console:

```json
{
  "type": "console_connect",
  "vm_id": "vm-123456"
}
```

### Event Stream

Subscribe to VM events:

```json
{
  "type": "subscribe",
  "events": ["vm.state_changed", "vm.console_output"]
}
```

## Examples

### Python Client Example

```python
import requests

class VBoxMCPClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def list_vms(self):
        response = requests.get(
            f"{self.base_url}/vms",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_vm(self, name, memory_mb, cpus, storage_gb):
        data = {
            'name': name,
            'memory_mb': memory_mb,
            'cpus': cpus,
            'storage_gb': storage_gb,
            'os_type': 'Ubuntu_64'
        }
        
        response = requests.post(
            f"{self.base_url}/vms",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def start_vm(self, vm_id):
        response = requests.post(
            f"{self.base_url}/vms/{vm_id}/start",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = VBoxMCPClient("http://localhost:8000/api/v1", "your-api-key")
print(client.list_vms())
```

### cURL Examples

List all VMs:

```bash
curl -X GET "http://localhost:8000/api/v1/vms" \
  -H "X-API-Key: your-api-key"
```

Create a new VM:

```bash
curl -X POST "http://localhost:8000/api/v1/vms" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-vm",
    "memory_mb": 2048,
    "cpus": 2,
    "storage_gb": 30,
    "os_type": "Ubuntu_64"
  }'
```

Start a VM:

```bash
curl -X POST "http://localhost:8000/api/v1/vms/test-vm/start" \
  -H "X-API-Key: your-api-key"
```
