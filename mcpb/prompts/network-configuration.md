# Network Configuration Prompt

## Purpose
Guide users through VirtualBox network configuration options and best practices.

## Network Types Overview

### NAT (Network Address Translation)
**When to Use**:
- VM needs internet access
- Simplest configuration
- No additional network setup required
- Default for most VMs

**Characteristics**:
- ✅ VM can access internet
- ✅ Host can access VM via port forwarding
- ❌ Other VMs can't access this VM directly
- ❌ Host can't access VM without port forwarding

**Configuration**:
```
Network Type: NAT
Port Forwarding Rules (optional):
- SSH: Host 2222 → Guest 22
- HTTP: Host 8080 → Guest 80
- Custom: Host XXXX → Guest YYYY
```

### Bridged Adapter
**When to Use**:
- VM needs to appear as separate machine on network
- VM needs to be accessible from other network devices
- Running servers that need direct network access

**Characteristics**:
- ✅ VM gets IP from network DHCP
- ✅ Accessible from any device on network
- ✅ Acts like physical computer
- ⚠️ May require network admin permissions

**Configuration**:
```
Network Type: Bridged
Bridge Adapter: [Select your physical adapter]
Promiscuous Mode: Deny (security)
```

### Host-Only Adapter
**When to Use**:
- VM needs to communicate with host
- Isolated network for development/testing
- SSH access without port forwarding

**Characteristics**:
- ✅ VM can communicate with host
- ✅ VMs on same host-only network can communicate
- ❌ No internet access (unless NAT also configured)
- ✅ Completely isolated from external network

**Configuration**:
```
Network Type: Host-Only
Host-Only Network: vboxnet0 (or create new)
IP Configuration: DHCP or Static
```

### Internal Network
**When to Use**:
- Multiple VMs need to communicate privately
- Completely isolated environment
- Security testing, malware analysis

**Characteristics**:
- ✅ VMs on same internal network can communicate
- ❌ No host access
- ❌ No internet access
- ✅ Completely isolated

**Configuration**:
```
Network Type: Internal Network
Network Name: intnet (or custom name)
```

### Not Attached
**When to Use**:
- Complete network isolation
- Offline VMs
- Security testing

## Multi-Adapter Configurations

VMs can have up to 4 network adapters simultaneously. Common combinations:

### Web Development VM
```
Adapter 1: NAT (internet access)
  - Port Forwarding: 3000→3000, 8080→8080
Adapter 2: Host-Only (SSH/direct access)
  - IP: 192.168.56.10
Adapter 3-4: Not attached
```

### Multi-Tier Application
```
Web Server VM:
  Adapter 1: NAT (internet for updates)
  Adapter 2: Internal "app-network" (talk to app server)

App Server VM:
  Adapter 1: Internal "app-network" (receive from web)
  Adapter 2: Internal "db-network" (talk to database)

Database Server VM:
  Adapter 1: Internal "db-network" (isolated database)
```

### Isolated Test Lab
```
All VMs:
  Adapter 1: Internal "testlab"
  
Router VM (if needed):
  Adapter 1: Internal "testlab"
  Adapter 2: NAT (controlled internet gateway)
```

## Port Forwarding Best Practices

### Common Port Forwards
```
SSH:        Host 2222 → Guest 22
HTTP:       Host 8080 → Guest 80
HTTPS:      Host 8443 → Guest 443
RDP:        Host 3389 → Guest 3389
MySQL:      Host 3306 → Guest 3306
PostgreSQL: Host 5432 → Guest 5432
MongoDB:    Host 27017 → Guest 27017
Redis:      Host 6379 → Guest 6379
```

### Port Forward Rules
- Use unique host ports for each VM
- Document all port forwards
- Use high-numbered ports (>1024) to avoid conflicts
- Test connectivity after creating rules

## Troubleshooting Network Issues

### VM Can't Access Internet (NAT)
1. Check adapter is enabled
2. Verify "Cable Connected" is checked
3. Test with ping: `ping 8.8.8.8`
4. Check DNS: `ping google.com`
5. Restart VM network service

### Can't SSH into VM
1. Verify SSH is installed and running in guest
2. Check port forwarding rule exists
3. Test connection: `ssh -p 2222 user@localhost`
4. Check firewall rules in guest
5. Verify SSH service is listening on port 22

### VMs Can't Communicate (Internal Network)
1. Verify both VMs on same internal network name
2. Check adapters are enabled
3. Configure static IPs or verify DHCP
4. Test with ping between VMs
5. Check firewall rules

## Example Interaction

**User**: "I want my web server VM to have internet access but also be accessible from my host machine"

**Assistant**:
"Perfect! This is a common scenario. I'll configure a dual-adapter setup:

**Adapter 1 - NAT (Internet Access)**
- Provides internet connectivity for the VM
- For package updates, downloads, etc.
- Port forwarding for web access from host

**Adapter 2 - Host-Only (Direct Access)**
- Allows SSH and direct communication
- Get dedicated IP like 192.168.56.10
- No port forwarding needed

**Configuration**:
1. Set up NAT on adapter 1 with port forwarding:
   - 8080→80 (HTTP)
   - 2222→22 (SSH backup)
2. Set up Host-Only on adapter 2:
   - Static IP: 192.168.56.10
   - Primary SSH access

**Result**:
- Access web server: http://localhost:8080
- SSH directly: ssh user@192.168.56.10
- VM has full internet access
- Clean, professional setup

Shall I configure this for you?"

