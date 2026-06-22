# Performance Tuning Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Host System Optimization](#host-system-optimization)
3. [VM Configuration](#vm-configuration)
4. [Storage Optimization](#storage-optimization)
5. [Network Optimization](#network-optimization)
6. [Memory Management](#memory-management)
7. [CPU Optimization](#cpu-optimization)
8. [I/O Performance](#io-performance)
9. [Graphics Performance](#graphics-performance)
10. [Benchmarking](#benchmarking)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | 64-bit processor with hardware virtualization (Intel VT-x/AMD-V) |
| RAM | 8GB (16GB recommended) |
| Storage | 50GB free space (SSD recommended) |
| OS | Linux, Windows 10/11, or macOS 10.15+ |
| VirtualBox | Version 7.0 or later |

### Recommended for Production

| Component | Recommendation |
|-----------|----------------|
| CPU | 8+ cores with nested virtualization |
| RAM | 32GB+ |
| Storage | NVMe SSD with 100GB+ free space |
| Network | 10Gbps network interface |
| OS | Linux with a recent kernel (5.15+ for best performance) |

## Host System Optimization

### Kernel Parameters

For Linux hosts, tune these kernel parameters in `/etc/sysctl.conf`:

```bash
# Increase system file descriptor limit
fs.file-max = 1000000

# Increase the maximum number of memory map areas a process may have
vm.max_map_count = 262144

# Increase the maximum number of open files
fs.nr_open = 1000000

# Network tuning
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 30000
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# Virtual memory settings
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2
vm.overcommit_memory = 1
```

Apply the changes:

```bash
sudo sysctl -p
```

### CPU Governor

Set the CPU governor to "performance" mode:

```bash
# Check current governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set to performance mode
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee $cpu
done

# Make it persistent
sudo apt install cpufrequtils
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
```

### Huge Pages

Enable huge pages for better memory performance:

```bash
# Check current huge pages
grep Huge /proc/meminfo

# Allocate 1024 huge pages (2MB each = 2GB total)
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Make it persistent
echo "vm.nr_hugepages = 1024" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## VM Configuration

### Basic VM Settings

```python
# Optimal VM configuration for performance
vm_config = {
    "name": "high-perf-vm",
    "os_type": "Ubuntu_64",
    "memory_mb": 16384,  # 16GB
    "cpus": 8,
    "nested_virt": True,  # For nested virtualization
    "paravirt_provider": "kvm",  # Or 'hyperv' for Windows guests
    "chipset": "ich9",  # Modern chipset
    "firmware": "efi",  # UEFI firmware
    "accelerate3d": True,  # Enable 3D acceleration if needed
    "accelerate2dvideo": True,  # Enable 2D video acceleration
    "vram_mb": 128,  # Video memory
    "io_apic": True,  # I/O APIC
    "pae": True,  # PAE/NX
    "hpet": True,  # High Precision Event Timer
    "rtc_use_utc": True,  # RTC in UTC
    "hwvirtex": True,  # Hardware virtualization
    "nestedpaging": True,  # Nested paging
    "largepages": True,  # Use large pages
    "vtxvpid": True,  # VPID
    "vtxux": True,  # Unrestricted guest
    "ioapic": "x2apic",  # Advanced Programmable Interrupt Controller
    "x2apic": True,  # x2APIC
    "paravirt": "kvm",  # Paravirtualization interface
    "graphics_controller": "vmsvga",  # Graphics controller
    "usb_controller": "xhci",  # USB 3.0 controller
    "audio_controller": "hda",  # Audio controller
    "network_adapters": [
        {
            "enabled": True,
            "type": "82540EM",
            "mode": "bridged",
            "promiscuous": "deny",
            "bandwidth_limit": 0,  # No limit
            "cable_connected": True
        }
    ],
    "storage_controllers": [
        {
            "name": "SATA Controller",
            "type": "sata",
            "port_count": 6,
            "bootable": True,
            "use_host_io_cache": False,
            "host_iocache": False
        }
    ]
}
```

### CPU Pinning

Pin VMs to specific CPU cores to reduce context switching:

```python
# Pin VM to specific CPU cores (0-3, 8-11)
manager.modify_vm("high-perf-vm", {
    "cpu_affinity": [0, 1, 2, 3, 8, 9, 10, 11],
    "cpu_hot_plug": False
})
```

### Memory Ballooning

Enable memory ballooning for dynamic memory management:

```python
# Enable memory ballooning
manager.modify_vm("high-perf-vm", {
    "memory_balloon_size": 256,  # MB
    "memory_ballooning": True
})
```

## Storage Optimization

### Disk Configuration

```python
# Create and attach an optimized disk
disk_config = {
    "path": "/path/to/disk.vdi",
    "size_gb": 100,
    "format": "vdi",
    "variant": "standard",
    "type": "normal",
    "solid": False,  # Don't pre-allocate
    "split": False,  # Don't split into 2GB files
    "medium_type": "ssd"  # Mark as SSD
}

manager.create_disk(**disk_config)

# Attach with optimal settings
manager.attach_disk(
    vm_name="high-perf-vm",
    disk_path=disk_config["path"],
    controller="SATA Controller",
    port=0,
    device=0,
    disk_type="hdd",
    non_rotational=True,  # For SSDs
    discard=True,  # Enable TRIM
    bandwidth_group="fast-storage"
)
```

### Disk I/O Tuning

```python
# Set I/O bandwidth limits
manager.set_io_bandwidth(
    vm_name="high-perf-vm",
    group_name="fast-storage",
    max_mb_per_sec=500  # 500 MB/s limit
)

# Configure I/O cache
manager.modify_vm("high-perf-vm", {
    "io_cache": True,  # Enable I/O cache
    "io_cache_size": 128,  # MB
    "io_bandwidth_max": 1000,  # 1000 MB/s
    "io_bandwidth_control": True
})
```

### Filesystem Optimization

For Linux guests, optimize the filesystem:

```bash
# Optimize ext4 filesystem
mkfs.ext4 -E lazy_itable_init=0,lazy_journal_init=0 /dev/sdX

# Mount with optimal options in /etc/fstab
# noatime - Don't update access times
# data=writeback - Faster, but less safe
# barrier=0 - Disable barriers for better performance (use with caution)
# commit=60 - Commit data every 60 seconds
UUID=xxx / ext4 defaults,noatime,data=writeback,barrier=0,commit=60 0 1
```

## Network Optimization

### Network Adapter Settings

```python
# Configure optimal network adapter
manager.modify_network_adapter(
    vm_name="high-perf-vm",
    slot=0,
    properties={
        "type": "virtio-net",  # Use virtio for best performance
        "cable_connected": True,
        "bandwidth_limit": 0,  # No limit
        "promiscuous_mode": "deny",
        "mac_address": "auto"
    }
)
```

### Network Modes

Choose the right network mode for your use case:

1. **Bridged**: Best performance, VM gets its own IP on the network
2. **NAT**: Default, good for most use cases
3. **Host-Only**: For host-VM communication only
4. **Internal**: For VM-VM communication only

```python
# Set network mode
manager.set_network_mode(
    vm_name="high-perf-vm",
    adapter_id=0,
    mode="bridged",
    bridge_adapter="eth0"  # Or your network interface
)
```

### Jumbo Frames

For high-performance networking, enable jumbo frames:

```bash
# On the host
ifconfig eth0 mtu 9000

# In the guest (Linux)
ifconfig eth0 mtu 9000

# Make it persistent in /etc/network/interfaces
iface eth0 inet static
    mtu 9000
```

## Memory Management

### Memory Allocation

```python
# Allocate memory with 1GB overhead
manager.modify_vm("high-perf-vm", {
    "memory_mb": 16384,  # 16GB
    "memory_overhead_mb": 1024,  # 1GB overhead
    "memory_ballooning": True,
    "page_fusion": False  # Disable for better performance
})
```

### Huge Pages

Enable huge pages in the guest OS:

```bash
# In the guest OS (Linux)
echo "vm.nr_hugepages = 8192" >> /etc/sysctl.conf
sysctl -p

# Mount huge pages
echo "huge /dev/hugepages hugetlbfs defaults 0 0" >> /etc/fstab
mount -a
```

## CPU Optimization

### CPU Allocation

```python
# Allocate CPU resources
manager.modify_vm("high-perf-vm", {
    "cpus": 8,
    "cpu_hot_plug": False,  # Disable for better performance
    "cpu_execution_cap": 100,  # 100% of allocated CPUs
    "cpu_profile": "host",  # Match host CPU
    "nested_hw_virt": True,  # Nested virtualization
    "pae": True,  # PAE/NX
    "long_mode": True,  # 64-bit mode
    "ibpb_on_vm_entry": True,  # Security feature
    "ibpb_on_vm_exit": True,
    "spec_ctrl": True  # Spectre mitigations
})
```

### CPU Pinning

Pin VM vCPUs to physical CPU cores:

```python
# Pin vCPUs 0-3 to physical CPUs 0,2,4,6
manager.set_cpu_affinity(
    vm_name="high-perf-vm",
    vcpu=0,
    cpuset="0,2,4,6"
)
```

## I/O Performance

### Disk I/O Scheduler

Use the right I/O scheduler for your workload:

```bash
# Check current scheduler
cat /sys/block/sda/queue/scheduler

# Set scheduler (for SSDs)
echo "none" > /sys/block/sda/queue/scheduler

# For HDDs
# echo "deadline" > /sys/block/sda/queue/scheduler
```

### Disk Cache Mode

Choose the right disk cache mode:

```python
# Set disk cache mode
manager.modify_disk(
    disk_path="/path/to/disk.vdi",
    cache="writethrough"  # Or "none", "writethrough", "writeback", "directsync", "unsafe"
)
```

### Disk I/O Tuning

```bash
# Increase disk read-ahead
blockdev --setra 8192 /dev/sda

# Increase I/O queue depth
echo 256 > /sys/block/sda/queue/nr_requests

# For SSDs, disable NCQ head-of-line blocking
echo 1 > /sys/block/sda/device/queue_depth
```

## Graphics Performance

### 3D Acceleration

```python
# Enable 3D acceleration
manager.modify_vm("high-perf-vm", {
    "accelerate3d": True,
    "accelerate2dvideo": True,
    "vram_mb": 256,  # Max VRAM
    "graphics_controller": "vmsvga",
    "monitor_count": 1,
    "accelerate3d_passthrough": False  # For GPU passthrough
})
```

### Remote Display

Optimize remote display performance:

```python
# Configure VRDP
manager.modify_vm("high-perf-vm", {
    "vrde": True,
    "vrde_port": 3389,
    "vrde_address": "0.0.0.0",
    "vrde_authtype": "null",
    "vrde_property": "TCP/Ports=3389",
    "vrde_extpack": "VNC",
    "vrde_reuse_connection": True,
    "vrde_video_channel": True,
    "vrde_video_channel_quality": 90
})
```

## Benchmarking

### CPU Benchmark

```bash
# Install sysbench
sudo apt install sysbench

# Run CPU benchmark
sysbench cpu --cpu-max-prime=20000 --threads=8 run
```

### Disk I/O Benchmark

```bash
# Test sequential read
fio --name=seqread --rw=read --direct=1 --ioengine=libaio --bs=1M --numjobs=4 --size=1G --runtime=60 --time_based --group_reporting

# Test random read
fio --name=randread --rw=randread --direct=1 --ioengine=libaio --bs=4k --numjobs=16 --size=1G --runtime=60 --time_based --group_reporting
```

### Network Benchmark

```bash
# Install iperf3
sudo apt install iperf3

# On server
iperf3 -s

# On client
iperf3 -c server-ip -t 60 -P 8
```

## Troubleshooting

### Common Issues

1. **High CPU Usage**
   - Check for CPU pinning conflicts
   - Verify CPU governor settings
   - Look for CPU-intensive processes

2. **Slow Disk I/O**
   - Check disk cache settings
   - Verify I/O scheduler
   - Look for disk errors

3. **Network Latency**
   - Check for network congestion
   - Verify MTU settings
   - Look for packet loss

### Performance Monitoring

```bash
# Monitor CPU usage
top -b -n 1 | head -n 20

# Monitor disk I/O
iotop -o

# Monitor network traffic
iftop -i eth0

# Monitor memory usage
free -m
```

## Best Practices

### General
- Always test changes in a non-production environment
- Monitor system performance after making changes
- Keep VirtualBox and guest additions up to date
- Use the latest stable kernel and drivers

### VM Configuration
- Allocate resources based on workload requirements
- Use the right disk and network controllers
- Enable only necessary hardware
- Use snapshots for testing configuration changes

### Storage
- Use SSDs for better I/O performance
- Enable TRIM for SSDs
- Use the right filesystem for your workload
- Consider using a separate disk for the OS and data

### Networking
- Use virtio network adapters when possible
- Enable jumbo frames for high-throughput workloads
- Consider SR-IOV for maximum network performance
- Use network bonding for redundancy and load balancing

### Security vs Performance
- Balance security settings with performance requirements
- Disable unnecessary security features for maximum performance
- Use hardware-based security features when available
- Regularly audit and update security settings

### Monitoring and Maintenance
- Set up performance monitoring
- Regularly check system logs
- Perform regular maintenance and updates
- Have a rollback plan for configuration changes

By following these guidelines, you can achieve optimal performance for your virtualization-mcp deployment. Remember to test any changes in a controlled environment before applying them to production systems.



