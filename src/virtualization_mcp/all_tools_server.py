"""
virtualization-mcp — FastMCP 3.2 entrypoint.

Registers all portmanteau tools and runs stdio transport.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from virtualization_mcp.config import configure_logging, settings
from virtualization_mcp.tools.register_tools import register_all_tools

configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name=settings.APP_NAME,
    version=settings.APP_VERSION,
    instructions=(
        "VirtualBox & Hyper-V VM management, Docker sandbox execution, "
        "snapshots, networking, and storage. "
        "Use vm_management for VM lifecycle, sandbox_management for isolated "
        "code execution, snapshot_management for save/restore points, "
        "network_management for host-only and NAT networks, "
        "storage_management for disks and controllers, "
        "hyperv_management for Hyper-V operations (Windows only), "
        "discovery_management to find VMs and providers, "
        "system_management for VirtualBox host info and OS types."
    ),
)

# Skills
_skills_dir = Path(__file__).resolve().parent / "skills"
if _skills_dir.is_dir():
    mcp.add_provider(SkillsDirectoryProvider(roots=[_skills_dir]))
    logger.info("Skills provider registered")

# Prompts
try:
    from virtualization_mcp.prompts import register_prompts

    register_prompts(mcp)
    logger.info("Prompts registered")
except ImportError:
    pass

# Tools
register_all_tools(mcp)
logger.info("All portmanteau tools registered")


def start_mcp_server(host: str | None = None, port: int | None = None) -> FastMCP:
    """Return the process-wide FastMCP instance (tools are registered at import time).

    ``host`` and ``port`` exist for older callers (e.g. run scripts); they are ignored because
    this entrypoint uses stdio via :func:`main`.
    """
    if host is not None or port is not None:
        logger.debug("start_mcp_server: host=%r port=%r ignored (stdio transport)", host, port)
    return mcp


# Hyper-V plugin (Windows only)
if sys.platform == "win32":
    try:
        from virtualization_mcp.plugins import initialize_plugins  # noqa: F401

        logger.info("Hyper-V plugin available")
    except ImportError as e:
        logger.debug(f"Hyper-V plugin not available: {e}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="VirtualBox MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http"], help="Transport mode")
    parser.add_argument(
        "--http", action="store_const", const="http", dest="transport", help="Alias for --transport http"
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")  # noqa: S104
    parser.add_argument("--port", type=int, default=10702, help="HTTP port")
    args = parser.parse_args()

    try:
        if args.transport == "http":
            logger.info(f"Starting HTTP server on {args.host}:{args.port}")
            app = mcp.http_app()
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            @app.get("/health")
            async def health():
                return {"status": "ok", "server": settings.APP_NAME}

            mcp.run(transport="http", host=args.host, port=args.port)
        else:
            mcp.run(transport="stdio")
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
