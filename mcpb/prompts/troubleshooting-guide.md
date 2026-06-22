# VM Troubleshooting Guide Prompt

## Purpose
Systematic approach to diagnosing and resolving virtual machine issues.

## Diagnostic Framework

### 1. Gather Information
Always start with:
- VM name and current state
- Recent changes or operations
- Error messages (if any)
- Host system resources

### 2. Check Common Issues
Systematically verify:
- VM state and configuration
- Resource availability
- Network connectivity
- Disk space and health
- VirtualBox installation

### 3. Apply Solutions
- Provide step-by-step fixes
- Explain why each step works
- Offer alternatives if primary solution fails
- Verify fix with testing

### 4. Prevent Recurrence
- Explain root cause
- Recommend preventive measures
- Suggest monitoring or alerts
- Document the solution

## Common Problems and Solutions

### Problem: "VM Won't Start"

**Diagnostic Steps**:
1. Get VM info to check current state
2. Check if VM is in "Saved" or "Aborted" state
3. Verify VT-x/AMD-V is enabled in BIOS
4. Check host resources (RAM, disk space)
5. Review VirtualBox logs

**Solutions**:
- **Saved State**: Use resume instead of start
- **Aborted State**: Reset the VM
- **Resource Conflict**: Close other VMs, free up RAM
- **VT-x Locked**: Disable Hyper-V or other hypervisors
- **Disk Full**: Free up host disk space

### Problem: "VM Running But Unresponsive"

**Diagnostic Steps**:
1. Check host CPU and memory usage
2. Check VM's assigned resources
3. Verify Guest Additions installed
4. Check for disk I/O bottlenecks

**Solutions**:
- **Host Overloaded**: Close other applications, increase VM priority
- **Insufficient Resources**: Stop VM, increase RAM/CPU allocation
- **Disk Thrashing**: Add more RAM, use SSD for VM storage
- **Network Lag**: Check network configuration, try different adapter type

### Problem: "Can't Connect to VM Network Services"

**Diagnostic Steps**:
1. Check VM network adapter configuration
2. Verify service is running in guest
3. Check port forwarding rules (if NAT)
4. Test connectivity from guest (ping, curl)
5. Check firewall rules (host and guest)

**Solutions**:
- **NAT Issue**: Set up port forwarding correctly
- **Bridged Issue**: Check DHCP, try static IP
- **Firewall**: Open required ports in guest/host
- **Service Not Running**: Start service in guest, verify port listening

### Problem: "Snapshots Take Too Long"

**Diagnostic Steps**:
1. Check snapshot size and VM disk usage
2. Verify host disk performance
3. Check if VM is running (longer for running VMs)
4. Review snapshot chain depth

**Solutions**:
- **Large VM**: Stop VM before snapshot (much faster)
- **Snapshot Chain**: Merge old snapshots
- **Slow Disk**: Move VM to SSD
- **Space Issues**: Clean up old snapshots

### Problem: "Disk Space Running Out"

**Diagnostic Steps**:
1. List all snapshots for VMs
2. Check VM disk sizes (virtual vs actual)
3. Review number of VMs and their disk usage
4. Check for crashed VM log files

**Solutions**:
- **Too Many Snapshots**: Delete old unnecessary snapshots
- **Disk Not Compact**: Compact virtual disks
- **Unused VMs**: Delete or export unused VMs
- **Log Files**: Clear VirtualBox log files

### Problem: "VM Performance Degraded"

**Diagnostic Steps**:
1. Get VM metrics and performance data
2. Check host resource utilization
3. Review VM resource allocation
4. Check for long snapshot chains
5. Verify Guest Additions installed

**Solutions**:
- **Under-resourced**: Increase RAM/CPU allocation
- **Snapshot Chain**: Merge snapshots
- **No Guest Additions**: Install Guest Additions
- **Host Overloaded**: Close other apps, run fewer VMs
- **Disk I/O**: Move to SSD, reduce disk activity

## Troubleshooting Workflow

### Step 1: Quick Checks (2 minutes)
```
1. Get VM info → Check state, configuration
2. Get host info → Verify resources available
3. Check recent operations → Identify what changed
```

### Step 2: Targeted Diagnostics (5 minutes)
```
Based on problem type:
- Startup issues → Check state, resources, logs
- Network issues → Test connectivity, check configuration
- Performance issues → Monitor resources, check allocation
- Storage issues → Check disk space, snapshot chains
```

### Step 3: Apply Fix (10 minutes)
```
1. Implement recommended solution
2. Verify fix worked
3. Test VM functionality
4. Document the resolution
```

### Step 4: Prevention (5 minutes)
```
1. Create snapshot if now stable
2. Implement preventive measures
3. Set up monitoring if applicable
4. Document for future reference
```

## Example Interaction

**User**: "My VM is really slow, what should I check?"

**Assistant**:
"I'll help you diagnose the performance issue systematically.

**Step 1: Gather Information**
Let me get the VM info and performance metrics first.

*[Calls get_vm_info and get_vm_metrics]*

**Analysis:**
- VM Name: DevEnv
- Current State: Running
- Allocated: 2 GB RAM, 1 CPU
- Host Available: 16 GB RAM, 8 CPUs
- Disk: 25 GB VDI (18 GB used)
- Snapshots: 12 snapshots (potential issue!)

**Identified Issues:**
1. ⚠️ Only 2 GB RAM - may be insufficient for development
2. ⚠️ Only 1 CPU - limiting performance
3. ❌ 12 snapshots - creating long snapshot chain (slowing disk I/O)

**Recommended Solutions:**

**Immediate (Stop VM first)**:
1. Increase RAM to 4 GB: `modify_vm DevEnv memory_mb=4096`
2. Increase CPUs to 2: `modify_vm DevEnv cpu_count=2`
3. Merge old snapshots: Review and delete snapshots older than 30 days

**Long-term**:
1. Install Guest Additions if not already installed
2. Move VM to SSD if currently on HDD
3. Implement snapshot cleanup policy (keep last 3-5)
4. Monitor performance regularly

Would you like me to stop the VM and apply these changes?"

