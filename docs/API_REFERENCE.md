# vboxmcp API Reference

## Table of Contents
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Error Handling](#error-handling)
- [API Endpoints](#api-endpoints)
  - [VM Management](#vm-management)
  - [Snapshot Management](#snapshot-management)
  - [Network Management](#network-management)
  - [Storage Management](#storage-management)
  - [Monitoring](#monitoring)

## Authentication

All API requests require authentication using an API key. Include the key in the `X-API-Key` header.

```http
GET /api/vms
X-API-Key: your-api-key-here
```

## Base URL

All API endpoints are prefixed with `/api`.

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Additional error details"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Something went wrong |

## API Endpoints

### VM Management

#### List All VMs

```http
GET /api/vms
```

**Query Parameters:**
- `state`: Filter VMs by state (running, stopped, paused, saved)

**Example Response:**
```json
{
  "vms": [
    {
      "id": "vm-123",
      "name": "ubuntu-server",
      "state": "running",
      "os_type": "Ubuntu_64",
      "memory_mb": 4096,
      "cpu_count": 2
    }
  ]
}
```

#### Get VM Details

```http
GET /api/vms/{vm_id}
```

**Path Parameters:**
- `vm_id`: ID of the virtual machine

**Example Response:**
```json
{
  "id": "vm-123",
  "name": "ubuntu-server",
  "state": "running",
  "os_type": "Ubuntu_64",
  "memory_mb": 4096,
  "cpu_count": 2,
  "storage_controllers": [
    {
      "name": "SATA Controller",
      "type": "IntelAhci",
      "port_count": 30
    }
  ],
  "network_adapters": [
    {
      "slot": 0,
      "enabled": true,
      "type": "82540EM",
      "mac_address": "08:00:27:00:00:01",
      "attachment_type": "NAT"
    }
  ]
}
```

#### Create VM

```http
POST /api/vms
Content-Type: application/json

{
  "name": "new-vm",
  "os_type": "Ubuntu_64",
  "memory_mb": 2048,
  "cpu_count": 2,
  "storage_gb": 20
}
```

**Request Body:**
- `name`: Name of the new VM (required)
- `os_type`: Type of guest OS (required)
- `memory_mb`: Memory in MB (required)
- `cpu_count`: Number of CPUs (required)
- `storage_gb`: Size of the main disk in GB (required)
- `network_type`: Type of network adapter (default: "NAT")

#### Start VM

```http
POST /api/vms/{vm_id}/start
Content-Type: application/json

{
  "headless": true
}
```

**Request Body:**
- `headless`: Start in headless mode (no UI)
- `wait_until_running`: Wait until VM is fully started

#### Stop VM

```http
POST /api/vms/{vm_id}/stop
Content-Type: application/json

{
  "force": false
}
```

**Request Body:**
- `force`: Force stop (equivalent to power off)

### Snapshot Management

#### List Snapshots

```http
GET /api/vms/{vm_id}/snapshots
```

**Example Response:**
```json
{
  "snapshots": [
    {
      "id": "snap-123",
      "name": "clean-install",
      "description": "Fresh OS installation",
      "created_at": "2025-01-01T12:00:00Z",
      "is_current": false
    }
  ]
}
```

#### Create Snapshot

```http
POST /api/vms/{vm_id}/snapshots
Content-Type: application/json

{
  "name": "pre-update",
  "description": "Before applying system updates"
}
```

#### Restore Snapshot

```http
POST /api/vms/{vm_id}/snapshots/{snapshot_id}/restore
```

### Network Management

#### List Network Adapters

```http
GET /api/vms/{vm_id}/network-adapters
```

#### Update Network Adapter

```http
PATCH /api/vms/{vm_id}/network-adapters/{slot}
Content-Type: application/json

{
  "enabled": true,
  "attachment_type": "bridged",
  "bridge_adapter": "eth0"
}
```

### Storage Management

#### List Storage Controllers

```http
GET /api/vms/{vm_id}/storage-controllers
```

#### Attach Disk

```http
POST /api/vms/{vm_id}/disks
Content-Type: application/json

{
  "type": "hdd",
  "size_gb": 50,
  "format": "vdi"
}
```

### Monitoring

#### Get VM Metrics

```http
GET /api/vms/{vm_id}/metrics
```

**Query Parameters:**
- `interval`: Time window for metrics (e.g., 1h, 5m)

**Example Response:**
```json
{
  "cpu_usage_percent": 15.5,
  "memory_usage_mb": 2048,
  "memory_available_mb": 2048,
  "disk_read_bytes": 1024000,
  "disk_write_bytes": 512000,
  "network_in_bytes": 2048000,
  "network_out_bytes": 1024000,
  "timestamp": "2025-08-05T08:00:00Z"
}
```

#### Get System Resources

```http
GET /api/system/resources
```

**Example Response:**
```json
{
  "cpu": {
    "cores": 8,
    "usage_percent": 25.5
  },
  "memory": {
    "total_mb": 32768,
    "available_mb": 16384,
    "used_percent": 50.0
  },
  "disk": {
    "total_gb": 1000,
    "free_gb": 500,
    "used_percent": 50.0
  },
  "network": {
    "interfaces": [
      {
        "name": "eth0",
        "bytes_sent": 1024000,
        "bytes_received": 2048000
      }
    ]
  }
}
```
