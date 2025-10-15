"""
Backup Tools for virtualization-mcp

This package provides functionality for managing VM backups with retention policies
and configuration management.
"""

from .backup_tools import (
    # Backup manager (stub for compatibility)
    backup_manager,
    delete_backup,
    get_backup_config,
    # Configuration helpers
    get_backup_dir,
    list_backups,
    save_backup_config,
)
from .backup_tools import (
    # Core functions
    create_backup_legacy as create_backup,
)

# For backward compatibility
__all__ = [
    "create_backup",
    "list_backups",
    "delete_backup",
    "restore_backup",
    "BackupManager",
    "backup_manager",
    "get_backup_dir",
    "get_backup_config",
    "save_backup_config",
]
