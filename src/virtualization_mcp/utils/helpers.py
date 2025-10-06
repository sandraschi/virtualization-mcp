"""
Helper functions for VBoxMCP.

This module provides utility functions used throughout the VBoxMCP application.
"""

import os
import platform
from pathlib import Path
from typing import Optional

def get_vbox_home() -> Path:
    """
    Get the VirtualBox home directory.
    
    Returns:
        Path: Path to the VirtualBox home directory.
        
    Raises:
        FileNotFoundError: If VirtualBox home directory cannot be determined.
    """
    system = platform.system().lower()
    
    if system == 'windows':
        # Default VirtualBox installation path on Windows
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        vbox_path = Path(program_files) / 'Oracle' / 'VirtualBox'
        
        # Check if VirtualBox is installed in Program Files (x86)
        if not vbox_path.exists() and 'ProgramFiles(x86)' in os.environ:
            vbox_path = Path(os.environ['ProgramFiles(x86)']) / 'Oracle' / 'VirtualBox'
    
    elif system == 'darwin':  # macOS
        vbox_path = Path('/Applications/VirtualBox.app/Contents/MacOS')
    
    else:  # Linux and other Unix-like systems
        vbox_path = Path('/usr/lib/virtualbox')
    
    # Verify the path exists
    if not vbox_path.exists():
        # Try to find it in the user's home directory
        user_home = Path.home()
        if system == 'windows':
            vbox_path = user_home / 'VirtualBox VMs'
        else:
            vbox_path = user_home / '.VirtualBox'
    
    # Ensure the directory exists
    vbox_path.mkdir(parents=True, exist_ok=True)
    return vbox_path

def get_vbox_vms_dir() -> Path:
    """
    Get the default directory where VirtualBox stores VMs.
    
    Returns:
        Path: Path to the VirtualBox VMs directory.
    """
    if platform.system().lower() == 'windows':
        # On Windows, VMs are typically stored in the user's home directory
        vms_dir = Path.home() / 'VirtualBox VMs'
    else:
        # On Unix-like systems, VMs are typically stored in ~/VirtualBox VMs
        vms_dir = Path.home() / 'VirtualBox VMs'
    
    # Ensure the directory exists
    vms_dir.mkdir(parents=True, exist_ok=True)
    return vms_dir

def ensure_dir_exists(path: Path) -> Path:
    """
    Ensure that the specified directory exists.
    
    Args:
        path: Path to the directory.
        
    Returns:
        Path: The same path, after ensuring it exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
