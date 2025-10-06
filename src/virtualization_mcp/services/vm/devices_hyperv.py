"""
Hyper-V Device Management Module

This module provides functionality for managing VM devices in a Hyper-V environment.
"""

import json
import subprocess
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HyperVDeviceManager:
    """Manages VM devices in a Hyper-V environment."""
    
    @staticmethod
    def list_devices(vm_name: str) -> List[Dict[str, Any]]:
        """
        List all devices for a Hyper-V VM.
        
        Args:
            vm_name: Name of the VM to list devices for
            
        Returns:
            List of device dictionaries, or empty list on error
        """
        try:
            # PowerShell script to get VM devices
            ps_script = f"""
$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop
$dvd = $vm | Get-DVDDrive
$nics = $vm | Get-VMNetworkAdapter
$hdd = $vm | Get-VMHardDiskDrive
$scsi = $vm | Get-VMScsiController

$devices = @()

# Add DVD drives
if ($dvd) {{
    $devices += $dvd | ForEach-Object {{
        [PSCustomObject]@{{
            Type = "DVD"
            Name = $_.Name
            Path = $_.Path
            ControllerNumber = $_.ControllerNumber
            ControllerLocation = $_.ControllerLocation
        }}
    }}
}}

# Add network adapters
if ($nics) {{
    $devices += $nics | ForEach-Object {{
        [PSCustomObject]@{{
            Type = "Network"
            Name = $_.Name
            SwitchName = $_.SwitchName
            MacAddress = $_.MacAddress
            Status = $_.Status
        }}
    }}
}}

# Add hard disks
if ($hdd) {{
    $devices += $hdd | ForEach-Object {{
        [PSCustomObject]@{{
            Type = "HardDisk"
            Name = $_.Name
            Path = $_.Path
            ControllerNumber = $_.ControllerNumber
            ControllerLocation = $_.ControllerLocation
            ControllerType = $_.ControllerType
        }}
    }}
}}

# Add SCSI controllers
if ($scsi) {{
    $devices += $scsi | ForEach-Object {{
        [PSCustomObject]@{{
            Type = "SCSIController"
            Name = $_.Name
            ControllerNumber = $_.ControllerNumber
        }}
    }}
}}

# Return the devices as JSON
$devices | ConvertTo-Json -Depth 10
"""
            
            # Execute the PowerShell script
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to list devices for VM {vm_name}: {result.stderr}")
                return []

            # Parse the JSON output
            devices = json.loads(result.stdout)
            
            # Convert to list of dicts if it's not already
            if not isinstance(devices, list):
                if isinstance(devices, dict):
                    return [devices]
                logger.warning(f"Unexpected device list format: {type(devices)}")
                return []
                    
            return devices
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PowerShell command failed: {e.stderr}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse device list JSON: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error listing devices for VM {vm_name}")
            return []



