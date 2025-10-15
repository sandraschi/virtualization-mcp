"""
Audio Settings Manager for VMs.

This module provides functionality to manage audio settings for virtual machines.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...plugins import register_plugin
from ...plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class AudioControllerType(str, Enum):
    """Supported audio controller types with compatibility notes:
    - HDA: Intel HD Audio (recommended for modern OSes)
    - AC97: Legacy controller for older OSes
    - SB16: SoundBlaster 16 emulation (for legacy applications)
    - NONE: No audio (for headless/servers)
    """

    HDA = "HDA"  # Intel HD Audio (default)
    AC97 = "AC97"  # Legacy
    SB16 = "SB16"  # Legacy SoundBlaster
    NONE = "None"  # No audio


class AudioDriverType(str, Enum):
    """Audio driver backends with platform support:
    - DirectSound: Windows default (recommended on Windows)
    - WASAPI: Windows Audio Session API (lower latency)
    - ALSA: Linux default
    - Pulse: Modern Linux systems
    - CoreAudio: macOS default
    - OSS: Legacy Unix
    - Null: No audio output (for testing)
    """

    DIRECT_SOUND = "DirectSound"
    WASAPI = "WASAPI"
    ALSA = "ALSA"
    PULSE = "Pulse"
    CORE_AUDIO = "CoreAudio"
    OSS = "OSS"
    NULL = "Null"


class AudioSettings(BaseModel):
    """Audio settings for a VM with optimal defaults.

    Key settings:
    - enabled: Master audio on/off
    - controller: Audio hardware emulation (HDA recommended)
    - driver: Host audio system to use (auto-detected by default)
    - buffer_size_ms: Audio buffer size in milliseconds (lower = less latency but more CPU)
    - volume: 0-100% volume level
    - properties: Advanced audio properties
    """

    enabled: bool = True
    controller: AudioControllerType = AudioControllerType.HDA
    driver: AudioDriverType | None = None  # Auto-detect based on host OS
    audio_input: bool = True  # Enable microphone by default
    audio_output: bool = True
    buffer_size_ms: int = Field(100, ge=20, le=500, description="Audio buffer size in milliseconds")
    volume: int = Field(80, ge=0, le=100, description="Volume level (0-100)")
    properties: dict[str, Any] = Field(
        default_factory=lambda: {
            "mixer": True,  # Enable software mixing
            "duplex": True,  # Full-duplex audio
            "samples_rate": 44100,  # CD quality
            "samples_size": 16,  # 16-bit audio
            "channels": 2,  # Stereo
        }
    )


@register_plugin("audio_settings")
class AudioSettingsManager(BasePlugin):
    """Manages audio settings for virtual machines."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the Audio Settings Manager."""
        super().__init__(config)
        self.router = APIRouter(prefix="/audio", tags=["audio"])
        self.setup_routes()

    def setup_routes(self):
        """Set up API routes for audio settings."""
        self.router.add_api_route(
            "/{vm_name}", self.get_audio_settings, methods=["GET"], response_model=AudioSettings
        )
        self.router.add_api_route(
            "/{vm_name}", self.update_audio_settings, methods=["PUT"], response_model=AudioSettings
        )

    async def get_audio_settings(self, vm_name: str) -> AudioSettings:
        """Get audio settings for a VM."""
        # Implementation would query the actual VM's audio settings
        return AudioSettings()

    async def update_audio_settings(self, vm_name: str, settings: AudioSettings) -> AudioSettings:
        """Update audio settings for a VM."""
        # Implementation would update the actual VM's audio settings
        return settings
