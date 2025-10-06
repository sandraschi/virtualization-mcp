"""
Backup Tools for VBoxMCP

This package provides functionality for managing VM backups with retention policies
and configuration management.
"""

from .backup_tools import (
    # Core functions
    create_backup_legacy as create_backup,
    list_backups,
    delete_backup,
    
    # Backup manager (stub for compatibility)
    backup_manager,
    
    # Configuration helpers
    get_backup_dir,
    get_backup_config,
    save_backup_config,
)

# For backward compatibility
__all__ = [
    'create_backup',
    'list_backups',
    'delete_backup',
    'restore_backup',
    'BackupManager',
    'backup_manager',
    'get_backup_dir',
    'get_backup_config',
    'save_backup_config',
]
