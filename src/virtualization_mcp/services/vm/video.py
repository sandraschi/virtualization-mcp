"""
Video Settings Manager for VMs.

This module provides functionality to manage video settings for virtual machines.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from ...plugins import register_plugin
from ...plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class GraphicsControllerType(str, Enum):
    """Supported graphics controller types.

    VirtualBox and Hyper-V support different graphics controllers with varying capabilities:
    - VBoxVGA: Default for most OSes, supports 2D video and 3D acceleration
    - VBoxSVGA: Newer controller with better Windows guest support
    - VMSVGA: Standard VMWare SVGA II controller for compatibility
    - VBoxVGA_EFI: VBoxVGA with EFI support
    - VBoxSVGA_EFI: VBoxSVGA with EFI support
    - VMSVGA_EFI: VMSVGA with EFI support
    - None: No graphics controller (for headless operation)
    """

    # VirtualBox specific
    VBOX_VGA = "VBoxVGA"
    VBOX_SVGA = "VBoxSVGA"
    VBOX_VGA_EFI = "VBoxVGA_EFI"
    VBOX_SVGA_EFI = "VBoxSVGA_EFI"

    # VMWare compatibility
    VMWARE_SVGA = "VMSVGA"
    VMWARE_SVGA_EFI = "VMSVGA_EFI"

    # No graphics
    NONE = "None"


class VideoModeType(str, Enum):
    """Supported video modes."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    ENABLED_3D = "enabled_3d"


class ResolutionPreset(str, Enum):
    """Common resolution presets."""

    HD_720P = "1280x720"
    FHD_1080P = "1920x1080"
    QHD_1440P = "2560x1440"
    UHD_4K = "3840x2160"
    ULTRAWIDE_3440 = "3440x1440"
    ULTRAWIDE_5120 = "5120x2160"
    CUSTOM = "custom"


class VideoSettings(BaseModel):
    """Video settings for a VM.

    Resolution and scaling:
    - resolution: Predefined resolution preset or custom resolution
    - custom_width/height: Used when resolution is set to CUSTOM
    - scale_factor: UI scaling (1.0 = 100%, 2.0 = 200%, etc.)
    - auto_resize: Allow guest to dynamically resize display
    - high_dpi: Enable high DPI support for Retina/HiDPI displays
    """

    enabled: bool = True

    # Resolution settings
    resolution: ResolutionPreset = ResolutionPreset.FHD_1080P
    custom_width: int = Field(1920, ge=640, le=8192)
    custom_height: int = Field(1080, ge=480, le=8192)
    auto_resize: bool = True
    high_dpi: bool = True

    # Performance settings
    vram_size_mb: int = Field(128, ge=16, le=256, description="Video memory in MB")
    monitor_count: int = Field(1, ge=1, le=4, description="Number of virtual monitors")
    accelerate_3d: bool = True
    graphics_controller: GraphicsControllerType = GraphicsControllerType.VBOX_SVGA
    video_mode: VideoModeType = VideoModeType.ENABLED
    scale_factor: float = Field(
        1.0, ge=0.1, le=4.0, description="Display scaling factor (1.0 = 100%)"
    )

    # Advanced settings
    frame_rate_limit: int | None = Field(
        None, ge=30, le=240, description="Maximum frame rate (None for unlimited)"
    )
    vsync: bool = True
    triple_buffering: bool = True
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("vram_size_mb")
    @classmethod
    def validate_vram_size(cls, v):
        """Ensure VRAM size is a power of 2."""
        if (v & (v - 1)) != 0:
            raise ValueError("VRAM size must be a power of 2")
        return v


@register_plugin("video_settings")
class VideoSettingsManager(BasePlugin):
    """Manages video settings for virtual machines."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the Video Settings Manager."""
        super().__init__(config)
        self.router = APIRouter(prefix="/video", tags=["video"])
        self.setup_routes()

    def setup_routes(self):
        """Set up API routes for video settings."""
        self.router.add_api_route(
            "/{vm_name}", self.get_video_settings, methods=["GET"], response_model=VideoSettings
        )
        self.router.add_api_route(
            "/{vm_name}", self.update_video_settings, methods=["PUT"], response_model=VideoSettings
        )

    async def get_video_settings(self, vm_name: str) -> VideoSettings:
        """Get video settings for a VM."""
        # Implementation would query the actual VM's video settings
        return VideoSettings()

    async def update_video_settings(self, vm_name: str, settings: VideoSettings) -> VideoSettings:
        """Update video settings for a VM."""
        # Implementation would update the actual VM's video settings
        return settings
