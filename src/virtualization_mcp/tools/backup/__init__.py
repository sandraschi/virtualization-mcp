"""
Backup Tools for virtualization-mcp

This package provides functionality for managing VM backups with retention policies
and configuration management.
"""

from .backup_tools import (
    # Backup manager exports
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
    "BackupManager",
    "backup_manager",
    "create_backup",
    "delete_backup",
    "get_backup_config",
    "get_backup_dir",
    "list_backups",
    "restore_backup",
    "save_backup_config",
]
