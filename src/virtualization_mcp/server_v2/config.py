"""Configuration management for the VBoxMCP server."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

@dataclass
class ServerConfig:
    """Server configuration settings."""
    
    # Server settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    log_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    
    # VirtualBox settings
    vbox_manage_path: Optional[str] = None
    default_vm_folder: Optional[str] = None
    
    # Plugin configuration
    plugins: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_workers: int = 1
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert string paths to Path objects
        if isinstance(self.base_dir, str):
            self.base_dir = Path(self.base_dir)
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)
        
        # Create directories if they don't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default VM folder if not specified
        if self.default_vm_folder is None:
            self.default_vm_folder = str(self.base_dir / "vms")


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load configuration from a file or environment variables.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        ServerConfig: Loaded configuration
    """
    # Start with default configuration
    config = ServerConfig()
    
    # Update from environment variables
    config.debug = os.environ.get("VBOXMCP_DEBUG", "false").lower() in ("true", "1", "t")
    
    if log_level := os.environ.get("VBOXMCP_LOG_LEVEL"):
        config.log_level = log_level.upper()
    
    if vbox_path := os.environ.get("VBOX_MANAGE_PATH"):
        config.vbox_manage_path = vbox_path
    
    if vm_folder := os.environ.get("VBOX_VM_FOLDER"):
        config.default_vm_folder = vm_folder
    
    # TODO: Load from config file if provided
    
    return config
