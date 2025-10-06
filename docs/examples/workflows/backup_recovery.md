# Backup and Recovery Workflow

This guide provides comprehensive strategies for backing up and recovering virtual machines managed by virtualization-mcp.

## Table of Contents

1. [Backup Strategies](#backup-strategies)
2. [Scheduled Backups](#scheduled-backups)
3. [Disaster Recovery](#disaster-recovery)
4. [Incremental Backups](#incremental-backups)
5. [Cloud Storage Integration](#cloud-storage-integration)
6. [Verification and Testing](#verification-and-testing)
7. [Automated Recovery](#automated-recovery)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Backup Strategies

### 1. Full VM Export (OVA/OVF)

```python
def export_vm(vm_name, output_dir):
    """Export a VM to OVA format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"{vm_name}_{timestamp}.ova")
    
    manager.export_vm(
        vm_name=vm_name,
        output_file=output_file,
        format="ova",  # or "ovf10" for OVF format
        manifest=True,
        include_iso=False
    )
    return output_file
```

### 2. Snapshot-Based Backups

```python
def create_backup_snapshot(vm_name, description):
    """Create a backup snapshot with timestamp."""
    snapshot_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    manager.create_snapshot(
        vm_name=vm_name,
        snapshot_name=snapshot_name,
        description=f"Backup: {description}",
        include_ram=False
    )
    return snapshot_name


def cleanup_old_snapshots(vm_name, keep_last=5):
    """Keep only the most recent snapshots."""
    snapshots = manager.list_snapshots(vm_name)
    
    if len(snapshots) > keep_last:
        # Sort by creation date (newest first)
        snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Delete older snapshots
        for snapshot in snapshots[keep_last:]:
            manager.delete_snapshot(vm_name, snapshot['name'])
```

### 3. Disk-Only Backups

```python
def backup_vm_disks(vm_name, backup_dir):
    """Backup only VM disks."""
    vm_info = manager.get_vm_info(vm_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_info = {
        'vm_name': vm_name,
        'timestamp': timestamp,
        'disks': []
    }
    
    # Create backup directory
    vm_backup_dir = os.path.join(backup_dir, f"{vm_name}_{timestamp}")
    os.makedirs(vm_backup_dir, exist_ok=True)
    
    # Backup VM configuration
    config_path = os.path.join(vm_backup_dir, f"{vm_name}.vbox")
    manager.export_vm_config(vm_name, config_path)
    
    # Backup each disk
    for disk in vm_info['storage_controllers']:
        for attachment in disk.get('attachments', []):
            if 'medium' in attachment and attachment['medium']:
                disk_path = attachment['medium']
                disk_name = os.path.basename(disk_path)
                backup_path = os.path.join(vm_backup_dir, disk_name)
                
                # Clone the disk to backup location
                manager.clone_disk(
                    source=disk_path,
                    target=backup_path,
                    format=os.path.splitext(disk_path)[1][1:],
                    variant="standard"
                )
                
                backup_info['disks'].append({
                    'original_path': disk_path,
                    'backup_path': backup_path,
                    'controller': disk['name'],
                    'port': attachment['port'],
                    'device': attachment['device']
                })
    
    # Save backup metadata
    with open(os.path.join(vm_backup_dir, 'backup_info.json'), 'w') as f:
        json.dump(backup_info, f, indent=2)
    
    return backup_info
```

## Scheduled Backups

### 1. Using Python's schedule Library

```python
import schedule
import time

def backup_job():
    """Backup all running VMs."""
    vms = manager.list_vms()
    backup_dir = "/path/to/backups"
    
    for vm in vms:
        if vm['state'] == 'running':
            # Create a snapshot backup
            snapshot_name = create_backup_snapshot(
                vm['name'],
                "Scheduled nightly backup"
            )
            
            # Export the VM
            export_vm(vm['name'], backup_dir)
            
            # Clean up old snapshots
            cleanup_old_snapshots(vm['name'], keep_last=7)

# Schedule daily backups at 2 AM
schedule.every().day.at("02:00").do(backup_job)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```

### 2. Using Windows Task Scheduler (Windows)

Create a Python script (`backup_vms.py`) and schedule it with Windows Task Scheduler:

```python
# backup_vms.py
if __name__ == "__main__":
    backup_job()
```

### 3. Using cron (Linux/macOS)

Add this line to your crontab to run the backup daily at 2 AM:

```bash
0 2 * * * /usr/bin/python3 /path/to/backup_vms.py >> /var/log/vm_backup.log 2>&1
```

## Disaster Recovery

### 1. Full VM Recovery from OVA/OVF

```python
def recover_vm_from_ova(ova_path, vm_name=None):
    """Recover a VM from an OVA file."""
    if not vm_name:
        # Extract VM name from OVA filename
        vm_name = os.path.basename(ova_path).rsplit('.', 1)[0]
    
    # Import the OVA
    manager.import_vm(
        ova_path=ova_path,
        vm_name=vm_name,
        options={
            'keep_all_macs': True,
            'keep_nat_macs': True,
            'keep_disk_names': True
        }
    )
    
    # Start the VM
    manager.start_vm(vm_name)
    
    return vm_name
```

### 2. Rollback to Snapshot

```python
def rollback_to_snapshot(vm_name, snapshot_name=None):
    """Rollback VM to a specific snapshot or the most recent one."""
    if not snapshot_name:
        # Get the most recent snapshot
        snapshots = manager.list_snapshots(vm_name)
        if not snapshots:
            raise ValueError(f"No snapshots found for VM {vm_name}")
        snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
        snapshot_name = snapshots[0]['name']
    
    # Restore the snapshot
    manager.restore_snapshot(
        vm_name=vm_name,
        snapshot_name=snapshot_name,
        start_vm=True
    )
    
    return snapshot_name
```

### 3. Recover from Disk Backup

```python
def recover_from_disk_backup(backup_dir, new_vm_name=None):
    """Recover a VM from a disk backup."""
    # Load backup metadata
    with open(os.path.join(backup_dir, 'backup_info.json')) as f:
        backup_info = json.load(f)
    
    vm_name = new_vm_name or backup_info['vm_name']
    
    # Create a new VM with the same configuration
    manager.import_vm_config(
        config_path=os.path.join(backup_dir, f"{backup_info['vm_name']}.vbox"),
        vm_name=vm_name
    )
    
    # Attach the backed-up disks
    for disk in backup_info['disks']:
        manager.attach_disk(
            vm_name=vm_name,
            disk_path=disk['backup_path'],
            controller=disk['controller'],
            port=disk['port'],
            device=disk['device']
        )
    
    return vm_name
```

## Incremental Backups

### 1. Using Differencing Disks

```python
def create_incremental_backup(vm_name, backup_dir):
    """Create an incremental backup using differencing disks."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    vm_info = manager.get_vm_info(vm_name)
    
    # Create backup directory
    backup_path = os.path.join(backup_dir, f"{vm_name}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    
    # Create differencing disks for each disk
    for disk in vm_info['storage_controllers']:
        for attachment in disk.get('attachments', []):
            if 'medium' in attachment and attachment['medium']:
                disk_path = attachment['medium']
                disk_name = os.path.basename(disk_path)
                
                # Create a differencing disk
                diff_disk = os.path.join(backup_path, f"diff_{disk_name}")
                manager.create_disk(
                    path=diff_disk,
                    size_gb=1,  # Size will be extended as needed
                    format=os.path.splitext(disk_path)[1][1:],
                    variant="diff"
                )
                
                # Set the parent disk
                manager.modify_disk(
                    disk_path=diff_disk,
                    parent=disk_path
                )
                
                # Update the VM to use the differencing disk
                manager.attach_disk(
                    vm_name=vm_name,
                    disk_path=diff_disk,
                    controller=disk['name'],
                    port=attachment['port'],
                    device=attachment['device']
                )
    
    return backup_path
```

## Cloud Storage Integration

### 1. Backup to AWS S3

```python
import boto3
from botocore.exceptions import ClientError

def backup_to_s3(local_path, bucket_name, s3_path=None):
    """Upload a backup to AWS S3."""
    s3_client = boto3.client('s3')
    
    if s3_path is None:
        s3_path = os.path.basename(local_path)
    
    try:
        if os.path.isfile(local_path):
            s3_client.upload_file(local_path, bucket_name, s3_path)
        elif os.path.isdir(local_path):
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, os.path.dirname(local_path))
                    s3_key = os.path.join(s3_path, relative_path).replace('\\', '/')
                    s3_client.upload_file(local_file, bucket_name, s3_key)
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False

def backup_vm_to_s3(vm_name, bucket_name):
    """Backup a VM to S3."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Export the VM
        ova_path = os.path.join(temp_dir, f"{vm_name}.ova")
        manager.export_vm(vm_name, ova_path)
        
        # Upload to S3
        s3_path = f"backups/{datetime.now().strftime('%Y/%m/%d')}/{vm_name}.ova"
        return backup_to_s3(ova_path, bucket_name, s3_path)
```

## Verification and Testing

### 1. Verify Backup Integrity

```python
def verify_backup(backup_path):
    """Verify the integrity of a backup."""
    if backup_path.endswith('.ova'):
        # Verify OVA file
        try:
            # Try to get VM info from OVA
            manager.get_ova_info(backup_path)
            return True
        except Exception as e:
            print(f"Error verifying OVA: {e}")
            return False
    elif os.path.isdir(backup_path):
        # Verify directory backup
        required_files = ['backup_info.json']
        for file in required_files:
            if not os.path.exists(os.path.join(backup_path, file)):
                print(f"Missing required file: {file}")
                return False
        return True
    return False
```

### 2. Test Recovery

```python
def test_recovery(backup_path, test_vm_name):
    """Test recovering a VM from backup."""
    try:
        if backup_path.endswith('.ova'):
            recover_vm_from_ova(backup_path, test_vm_name)
        elif os.path.isdir(backup_path):
            recover_from_disk_backup(backup_path, test_vm_name)
        
        # Start the VM
        manager.start_vm(test_vm_name, gui=False, headless=True)
        
        # Wait for boot
        time.sleep(60)
        
        # Check if VM is responsive
        try:
            manager.execute_command(test_vm_name, "echo 'Test successful'")
            print("Recovery test passed")
            return True
        except:
            print("Recovery test failed: VM is not responsive")
            return False
        finally:
            # Clean up test VM
            manager.poweroff_vm(test_vm_name)
            manager.delete_vm(test_vm_name, delete_files=True)
    except Exception as e:
        print(f"Recovery test failed: {e}")
        return False
```

## Automated Recovery

### 1. Monitoring and Auto-Recovery

```python
def monitor_and_recover():
    """Monitor VMs and recover if they fail."""
    vms = manager.list_vms()
    
    for vm in vms:
        try:
            # Check if VM is running
            if vm['state'] != 'running':
                print(f"VM {vm['name']} is not running. Attempting to start...")
                manager.start_vm(vm['name'])
                
                # If still not running, attempt recovery
                time.sleep(10)  # Wait for startup
                vm_info = manager.get_vm_info(vm['name'])
                if vm_info['state'] != 'running':
                    print(f"Failed to start {vm['name']}. Attempting recovery...")
                    recover_vm(vm['name'])
        except Exception as e:
            print(f"Error monitoring {vm['name']}: {e}")

def recover_vm(vm_name):
    """Attempt to recover a VM using the latest backup."""
    backup_dir = f"/path/to/backups/{vm_name}"
    latest_backup = get_latest_backup(backup_dir)
    
    if not latest_backup:
        print(f"No backup found for {vm_name}")
        return False
    
    print(f"Recovering {vm_name} from backup {latest_backup}")
    
    # Stop the VM if it's running
    try:
        manager.stop_vm(vm_name, force=True)
    except:
        pass
    
    # Remove the broken VM
    try:
        manager.delete_vm(vm_name, delete_files=False)
    except:
        pass
    
    # Restore from backup
    if latest_backup.endswith('.ova'):
        recover_vm_from_ova(latest_backup, vm_name)
    else:
        recover_from_disk_backup(latest_backup, vm_name)
    
    # Start the VM
    manager.start_vm(vm_name)
    return True

def get_latest_backup(backup_dir):
    """Find the most recent backup in the directory."""
    try:
        # Look for OVA files first
        ova_files = glob.glob(os.path.join(backup_dir, "*.ova"))
        if ova_files:
            return max(ova_files, key=os.path.getmtime)
        
        # Then look for directory backups
        dirs = [d for d in os.listdir(backup_dir) 
               if os.path.isdir(os.path.join(backup_dir, d))]
        if dirs:
            latest_dir = max(dirs, key=lambda d: os.path.getmtime(os.path.join(backup_dir, d)))
            return os.path.join(backup_dir, latest_dir)
    except Exception as e:
        print(f"Error finding latest backup: {e}")
    
    return None
```

## Best Practices

1. **3-2-1 Backup Rule**
   - Keep 3 copies of your data
   - Store on 2 different media
   - Keep 1 copy offsite

2. **Regular Testing**
   - Test recovery procedures regularly
   - Document recovery steps
   - Keep recovery documentation up to date

3. **Monitoring**
   - Monitor backup job success/failure
   - Set up alerts for backup failures
   - Monitor storage space for backup locations

4. **Security**
   - Encrypt sensitive backups
   - Use secure transfer methods
   - Implement access controls for backup storage

## Troubleshooting

### Common Issues

1. **Backup Fails**
   - Check available disk space
   - Verify file permissions
   - Ensure the VM is in a consistent state

2. **Recovery Fails**
   - Verify backup integrity
   - Check for compatibility issues
   - Ensure sufficient resources are available

3. **Performance Issues**
   - Schedule backups during off-peak hours
   - Consider using incremental backups
   - Optimize storage performance

## Next Steps

- [Performance Tuning](../advanced/performance_tuning.md)
- [Security Best Practices](../advanced/security.md)
- [Disaster Recovery Planning](../advanced/disaster_recovery.md)



