# Troubleshooting Guide

This guide helps you identify and resolve common issues with the VirtualBox MCP Server.

## Common Issues

### 1. VirtualBox Not Found

**Symptoms**
- `VBoxManage` command not found
- Errors about missing VirtualBox installation

**Solutions**
1. Verify VirtualBox is installed:
   ```bash
   # On Linux/macOS
   which VBoxManage
   
   # On Windows
   where VBoxManage
   ```

2. If not found, download and install VirtualBox from [virtualbox.org](https://www.virtualbox.org/)

3. Add VirtualBox to your PATH:
   - Linux/macOS: Add to `~/.bashrc` or `~/.zshrc`
     ```bash
     export PATH=$PATH:/usr/lib/virtualbox
     ```
   - Windows: Add to System Environment Variables
     1. Open System Properties > Advanced > Environment Variables
     2. Add `C:\Program Files\Oracle\VirtualBox` to PATH

### 2. Permission Denied Errors

**Symptoms**
- `VBoxManage: error: Could not create the directory`
- Permission denied when managing VMs

**Solutions**
1. Add your user to the `vboxusers` group:
   ```bash
   sudo usermod -aG vboxusers $USER
   ```

2. Log out and back in for changes to take effect

3. Verify permissions:
   ```bash
   groups $USER  # Should include vboxusers
   ```

### 3. VM Won't Start

**Symptoms**
- VM fails to start with various errors
- Stuck in "Starting" state

**Troubleshooting Steps**
1. Check VirtualBox logs:
   ```bash
   VBoxManage showvminfo <vm_name> --log 0
   ```

2. Common issues:
   - **VT-x/AMD-V not enabled**: Enable in BIOS/UEFI settings
   - **Insufficient permissions**: Check `vboxusers` group membership
   - **Corrupted VM**: Try recreating the VM

### 4. Network Issues

**Symptoms**
- VM can't access the internet
- Host can't connect to VM

**Troubleshooting**
1. Check VM network settings:
   ```bash
   VBoxManage showvminfo <vm_name> | grep -i network
   ```

2. Verify NAT networking:
   ```bash
   VBoxManage list natnets
   ```

3. Try different network modes:
   - NAT (default)
   - Bridged
   - Host-only

### 5. Performance Issues

**Symptoms**
- Slow VM performance
- High CPU/memory usage

**Optimization Tips**
1. Allocate more CPU cores:
   ```bash
   VBoxManage modifyvm <vm_name> --cpus <number>
   ```

2. Increase memory:
   ```bash
   VBoxManage modifyvm <vm_name> --memory <MB>
   ```

3. Enable 3D acceleration if supported:
   ```bash
   VBoxManage modifyvm <vm_name> --accelerate3d on
   ```

## Server Issues

### 1. Server Won't Start

**Check Logs**
```bash
tail -f /var/log/virtualization-mcp.log
```

**Common Causes**
- Port already in use
- Missing dependencies
- Configuration errors

### 2. Authentication Failures

**Verify Configuration**
1. Check `.env` for correct API key
2. Ensure `ENABLE_AUTH` is set correctly
3. Verify request headers include `Authorization: Bearer <key>`

## Windows-Specific Issues

### 1. Hyper-V Conflicts

**Symptoms**
- `VT-x is not available` errors
- VMs fail to start with virtualization errors

**Solutions**
1. Disable Hyper-V:
   ```powershell
   bcdedit /set hypervisorlaunchtype off
   ```
2. Reboot your computer

### 2. Windows Sandbox Issues

**Prerequisites**
- Windows 10 Pro/Enterprise/Education (build 18305 or later)
- Virtualization enabled in BIOS
- Hyper-V enabled

**Enable Hyper-V**
```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

## Logging and Debugging

### Enable Debug Logging

1. Edit `.env`:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Restart the server

### View Logs

```bash
# Linux/macOS
tail -f /var/log/virtualization-mcp.log

# Windows
Get-Content -Path "C:\ProgramData\virtualization-mcp\logs\virtualization-mcp.log" -Wait
```

## Common Error Messages

### "VBOX_E_OBJECT_NOT_FOUND"
- VM or snapshot doesn't exist
- Check name spelling and case sensitivity

### "VBOX_E_INVALID_VM_STATE"
- Operation not allowed in current VM state
- Try starting/stopping the VM first

### "VBOX_E_IPRT_ERROR"
- General VirtualBox error
- Check VirtualBox logs for details

## Getting Help

1. Check the logs for detailed error messages
2. Search the [GitHub Issues](https://github.com/yourusername/virtualization-mcp/issues)
3. If the issue persists, [open a new issue](https://github.com/yourusername/virtualization-mcp/issues/new) with:
   - Error messages
   - Log output
   - Steps to reproduce
   - Environment details (OS, VirtualBox version, etc.)

## Known Issues

### VirtualBox 7.0.0-7.0.4
- Memory management issues
- Recommended: Upgrade to VirtualBox 7.0.6 or later

### Windows 11 Hosts
- May require additional configuration for nested virtualization
- Ensure "Virtual Machine Platform" and "Windows Hypervisor Platform" are enabled

### Linux Hosts with Secure Boot
- May require signing VirtualBox kernel modules
- See [VirtualBox documentation](https://www.virtualbox.org/manual/ch02.html#install-linux-host) for details



