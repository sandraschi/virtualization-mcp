"""
Configuration management for the VirtualBox MCP server using Pydantic.
"""

import logging
import logging.handlers
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

# Import settings with fallback
try:
    from .settings import BaseSettings
except ImportError:
    # Create a basic BaseSettings class if import fails
    from pydantic import BaseModel

    class BaseSettings(BaseModel):
        debug: bool = False
        log_level: str = "INFO"
        host: str = "0.0.0.0"
        port: int = 8000


# Set up logging
logger = logging.getLogger(__name__)

# Load .env file if it exists
if (env_path := Path(".env")).exists():
    from dotenv import load_dotenv

    load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        validate_default=True,
        case_sensitive=True,
        env_nested_delimiter="__",
    )

    # Application settings
    APP_NAME: str = "virtualization_mcp"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # VirtualBox settings
    VBOX_MANAGE_PATH: Path | None = None
    DEFAULT_VM_FOLDER: Path | None = None
    VBOX_HOME: Path | None = None

    # Security
    API_KEY: str | None = None
    CORS_ORIGINS: list[str] = ["*"]

    # Timeouts and limits (in seconds)
    API_TIMEOUT: int = 30
    COMMAND_TIMEOUT: int = 60
    VM_START_TIMEOUT: int = 120
    VM_STOP_TIMEOUT: int = 60
    SNAPSHOT_TIMEOUT: int = 180
    VM_OPERATION_TIMEOUT: int = 300  # 5 minutes

    # Default VM settings
    DEFAULT_MEMORY_MB: int = 2048
    DEFAULT_DISK_GB: int = 20
    DEFAULT_NETWORK: str = "NAT"
    DEFAULT_OS_TYPE: str = "Ubuntu_64"

    # Plugin configuration
    PLUGINS: list[str] = ["network_analyzer", "backup"]

    # Feature flags
    ENABLE_EXPERIMENTAL_FEATURES: bool = False
    ENABLE_METRICS: bool = True
    
    # Tool registration mode
    # - "production": Only portmanteau tools (5 tools, cleaner for users)
    # - "testing" or "all": All individual tools + portmanteau (60+ tools)
    TOOL_MODE: str = "production"

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        if v is None:
            return "INFO"
        if isinstance(v, str):
            v = v.upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.warning(f"Invalid log level: {v}, defaulting to INFO")
            return "INFO"
        return v

    @field_validator("DEFAULT_VM_FOLDER", mode="before")
    @classmethod
    def set_default_vm_folder(cls, v):
        if v is not None:
            path = Path(v).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            return path

        # Default paths for different platforms
        default_paths = {
            "win32": Path(os.environ.get("USERPROFILE", "~"), "VirtualBox VMs"),
            "darwin": Path.home() / "VirtualBox VMs",
            "linux": Path.home() / "VirtualBox VMs",
        }

        path = default_paths.get(sys.platform, Path.home() / "VirtualBox VMs")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("VBOX_MANAGE_PATH", mode="before")
    @classmethod
    def set_vbox_manage_path(cls, v):
        if v is not None:
            path = Path(v)
            if path.exists():
                return path
            logger.warning(f"Specified VBoxManage path does not exist: {v}")

        # Auto-detect VBoxManage path
        paths = [
            Path("C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"),
            Path("C:\\Program Files (x86)\\Oracle\\VirtualBox\\VBoxManage.exe"),
            Path("/usr/bin/VBoxManage"),
            Path("/usr/local/bin/VBoxManage"),
            shutil.which("VBoxManage"),
        ]

        for path in paths:
            if path and Path(path).exists():
                logger.info(f"Auto-detected VBoxManage at: {path}")
                return str(Path(path).resolve())

        logger.warning("Could not find VBoxManage in standard locations")
        return None


# Global settings instance
settings = Settings()


def get_logs_dir() -> Path:
    """Get the directory for log files."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True, parents=True)
    return log_dir


def setup_file_handlers(logger_name: str, log_level: int) -> list[logging.Handler]:
    """Set up file handlers with rotation and formatting."""
    log_dir = get_logs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Main log file with rotation (10MB per file, keep 5 backups)
    log_file = log_dir / f"virtualization-mcp_{timestamp}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Error log file (only ERROR and above)
    error_file = log_dir / f"virtualization-mcp_error_{timestamp}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)

    # Set formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    return [file_handler, error_handler]


def setup_console_handler() -> logging.Handler:
    """Set up console handler for stderr output."""
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)  # Default to INFO for console

    # Color formatter for console
    class ColorFormatter(logging.Formatter):
        COLORS = {
            "WARNING": "\033[93m",  # Yellow
            "INFO": "\033[92m",  # Green
            "DEBUG": "\033[96m",  # Cyan
            "CRITICAL": "\033[91m",  # Red
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m",  # Reset
        }

        def format(self, record):
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            message = super().format(record)
            if color != self.COLORS["RESET"]:
                message = f"{color}{message}{self.COLORS['RESET']}"
            return message

    console_handler.setFormatter(
        ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    )

    return console_handler


def configure_logging():
    """Configure logging with rotation and multiple handlers."""
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Set up handlers
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handlers = setup_file_handlers("virtualization-mcp", log_level)

    # Add console handler in development or when explicitly enabled
    if settings.DEBUG or os.environ.get("ENABLE_CONSOLE_LOGGING", "true").lower() == "true":
        handlers.append(setup_console_handler())

    # Configure root logger
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    # Configure third-party loggers to reduce spam
    for logger_name in [
        "uvicorn",
        "fastapi",
        "asyncio",
        "mcp",
        "mcp.server",
        "mcp.server.lowlevel",
        "mcp.server.lowlevel.server",
        "fastmcp",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("=" * 80)


# Get VBoxManage path
def get_vbox_manage_path() -> Path:
    """Get the path to VBoxManage executable."""
    if settings.VBOX_MANAGE_PATH and settings.VBOX_MANAGE_PATH.exists():
        return settings.VBOX_MANAGE_PATH

    # Try to find VBoxManage in PATH
    vbox_manage = "VBoxManage"
    if sys.platform == "win32":
        vbox_manage += ".exe"

    vbox_path = shutil.which(vbox_manage)
    if vbox_path:
        return Path(vbox_path)

    raise RuntimeError(
        "VBoxManage not found. Please install VirtualBox "
        "or set VBOX_MANAGE_PATH in your environment."
    )


# Initialize logging when module is imported
configure_logging()

# Export commonly used settings as module-level constants
DEBUG = settings.DEBUG
LOG_LEVEL = settings.LOG_LEVEL

# Export project root path
project_root = Path(__file__).parent.parent.parent

# Alias for server_v2 compatibility
ServerConfig = Settings
