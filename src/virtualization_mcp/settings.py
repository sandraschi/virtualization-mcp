from pydantic import BaseModel, ConfigDict


class BaseSettings(BaseModel):
    # General settings
    debug: bool = False
    log_level: str = "INFO"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # VirtualBox settings
    vbox_home: str | None = None

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        validate_default=True,
        case_sensitive=True,
        env_nested_delimiter="__",
    )


# Create a default settings instance
settings = BaseSettings()
