# Network Configuration

## Overview

virtualization-mcp provides comprehensive networking capabilities for VirtualBox virtual machines, supporting various network modes and configurations to meet different use cases.

## Network Adapter Types

### Supported Adapter Types

- **PCnet-PCI II (Am79C970A)**: Legacy adapter for maximum compatibility
- **PCnet-FAST III (Am79C973)**: Default for most guests
- **Intel PRO/1000 MT Desktop (82540EM)**: Recommended for modern OSes
- **Intel PRO/1000 T Server (82543GC)**: For Windows guests
- **Intel PRO/1000 MT Server (82545EM)**: For high-performance networking
- **Paravirtualized Network (virtio-net)**: For best performance (requires guest additions)

## Network Modes

### 1. Not Attached

```python
# Configure network adapter as not attached
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    enabled=False
)
```

### 2. NAT (Network Address Translation)

```python
# Basic NAT configuration
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="nat",
    adapter_type="82540EM",
    cable_connected=True
)

# With port forwarding
manager.configure_nat_port_forwarding(
    vm_name="ubuntu-server",
    adapter_id=1,
    rules=[
        {
            "name": "SSH",
            "protocol": "tcp",
            "host_port": 2222,
            "guest_port": 22,
            "guest_ip": ""  # Empty for any guest IP
        },
        {
            "name": "HTTP",
            "protocol": "tcp",
            "host_port": 8080,
            "guest_port": 80
        }
    ]
)
```

### 3. NAT Network

```python
# Create a NAT network
manager.create_nat_network(
    name="MyNATNetwork",
    network="10.0.2.0/24",
    enable_dhcp=True,
    dhcp_min="10.0.2.3",
    dhcp_max="10.0.2.254"
)

# Configure VM to use NAT network
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="natnetwork",
    nat_network="MyNATNetwork"
)
```

### 4. Bridged Networking

```python
# Configure bridged networking
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="bridged",
    bridge_adapter="eth0"  # or "Ethernet" on Windows
)
```

### 5. Internal Network

```python
# Configure internal network
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="intnet",
    intnet="intnet1"
)

# Create multiple VMs on the same internal network
manager.configure_network_adapter(
    vm_name="vm2",
    adapter_id=1,
    mode="intnet",
    intnet="intnet1"
)
```

### 6. Host-Only Networking

```python
# Create a host-only network
hostonly_network = manager.create_hostonly_network(
    name="vboxnet0",
    ip="192.168.56.1",
    netmask="255.255.255.0",
    dhcp_enabled=True,
    lower_ip="192.168.56.100",
    upper_ip="192.168.56.200"
)

# Configure VM to use host-only network
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="hostonly",
    hostonly_network="vboxnet0"
)
```

### 7. Generic Networking

```python
# Configure generic networking (for special drivers)
manager.configure_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="generic",
    generic_driver="UDPTunnel",
    generic_properties={
        "sport": "10001",
        "dport": "10002",
        "daddress": "127.0.0.1"
    }
)
```

## Advanced Network Configuration

### Bandwidth Limiting

```python
# Enable bandwidth limiting
manager.set_bandwidth_limit(
    vm_name="ubuntu-server",
    adapter_id=1,
    kbps=1024,  # 1 Mbps limit
    mode="kbps"  # or "mbps"
)

# Disable bandwidth limiting
manager.disable_bandwidth_limit("ubuntu-server", adapter_id=1)
```

### Promiscuous Mode

```python
# Set promiscuous mode
manager.set_promiscuous_mode(
    vm_name="ubuntu-server",
    adapter_id=1,
    mode="allow-all"  # or "deny", "allow-vms", "allow-network"
)
```

### Port Forwarding

```python
# Add port forwarding rule
manager.add_port_forwarding(
    vm_name="ubuntu-server",
    rule_name="SSH",
    protocol="tcp",
    host_port=2222,
    guest_port=22,
    guest_ip=""  # Empty for any guest IP
)

# List port forwarding rules
rules = manager.list_port_forwarding("ubuntu-server")

# Remove port forwarding rule
manager.remove_port_forwarding("ubuntu-server", "SSH")
```

## Network Adapter Management

### Listing Network Adapters

```python
# List all network adapters for a VM
adapters = manager.list_network_adapters("ubuntu-server")

# Get detailed information about a specific adapter
adapter_info = manager.get_network_adapter_info(
    vm_name="ubuntu-server",
    adapter_id=1
)
```

### Modifying Network Adapters

```python
# Modify an existing network adapter
manager.modify_network_adapter(
    vm_name="ubuntu-server",
    adapter_id=1,
    properties={
        "cable_connected": True,
        "adapter_type": "82540EM",
        "mac_address": "auto"  # or specific MAC
    }
)

# Connect/disconnect network cable
manager.set_network_cable_connected("ubuntu-server", 1, True)
```

## Network Services

### DHCP Server

```python
# Configure DHCP server for a host-only network
manager.configure_dhcp_server(
    network_name="vboxnet0",
    enabled=True,
    server_ip="192.168.56.100",
    lower_ip="192.168.56.101",
    upper_ip="192.168.56.254",
    netmask="255.255.255.0"
)

# Disable DHCP server
manager.disable_dhcp_server("vboxnet0")
```

### DNS Server

```python
# Configure DNS server for a NAT network
manager.configure_dns_server(
    network_name="MyNATNetwork",
    dns_servers=["8.8.8.8", "8.8.4.4"],
    proxy_mode="off"  # or "auto", "manual"
)
```

## Best Practices

1. **Network Isolation**
   - Use host-only or internal networks for private communication
   - Implement proper firewall rules in guests
   - Consider using NAT networks for better isolation

2. **Performance**
   - Use paravirtualized network adapters when possible
   - Enable host I/O cache for better performance
   - Consider using bridged networking for maximum throughput

3. **Security**
   - Disable unnecessary network adapters
   - Use MAC address filtering when possible
   - Regularly update guest additions for security patches

## Troubleshooting

### Common Issues

1. **No Network Connectivity**
   - Verify the network adapter is enabled
   - Check cable connection status
   - Verify network mode and settings

2. **Slow Network Performance**
   - Check host network utilization
   - Try a different network adapter type
   - Disable bandwidth limiting if enabled

3. **Port Forwarding Not Working**
   - Verify the guest service is running
   - Check firewall settings on host and guest
   - Ensure no port conflicts on the host

## Next Steps

- [Snapshot Management](../concepts/snapshot_management.md)
- [Advanced Configuration](../advanced/performance_tuning.md)
- [Security Best Practices](../advanced/security.md)



