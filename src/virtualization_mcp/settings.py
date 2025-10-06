from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

class BaseSettings(BaseModel):
    # General settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # VirtualBox settings
    vbox_home: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='allow',
        validate_default=True,
        case_sensitive=True,
        env_nested_delimiter="__"
    )

# Create a default settings instance
settings = BaseSettings()



