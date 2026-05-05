"""
Windows Sandbox Plugin for virtualization-mcp

This module provides Windows Sandbox integration for virtualization-mcp.
"""

from .manager import WindowsSandboxHelper
from .portfolio_manager import PortfolioManager

__all__ = [
    "FileCopyOperation",
    "MappedFolder",
    "PortfolioManager",
    "SandboxConfig",
    "SandboxPortfolio",
    "SandboxState",
    "WindowsSandboxHelper",
]
