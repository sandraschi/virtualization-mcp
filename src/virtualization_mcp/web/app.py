"""
FastAPI web application for virtualization-mcp.

Provides HTTP/WebSocket interface for VM management alongside the MCP server.
Both servers share the same backend services.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import shared services
from ..config import settings
from ..services.service_manager import get_service_manager

logger = logging.getLogger(__name__)

# Base directories - calculate from current file location
# app.py is at: src/virtualization_mcp/web/app.py
# We need to go up to project root: src/virtualization_mcp/web -> src/virtualization_mcp -> src -> root
_current_file = Path(__file__).resolve()
BASE_DIR = _current_file.parent.parent.parent.parent  # Go up 4 levels to project root
WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Fallback: if web/ doesn't exist in root, try src-relative
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = BASE_DIR / "src" / "virtualization_mcp" / "web" / "templates"
if not STATIC_DIR.exists():
    STATIC_DIR = BASE_DIR / "src" / "virtualization_mcp" / "web" / "static"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Templates directory: {TEMPLATES_DIR}")
logger.info(f"Templates exists: {TEMPLATES_DIR.exists()}")

# Initialize templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create FastAPI app
app = FastAPI(
    title="Virtualization MCP - Web Interface",
    version=settings.APP_VERSION,
    description="Web interface for VirtualBox VM management",
    default_response_class=JSONResponse,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Get service manager (shared with MCP server)
# Initialize lazily to avoid import-time errors
_service_manager = None

def get_vm_service():
    """Get VM service, initializing if needed."""
    global _service_manager
    if _service_manager is None:
        _service_manager = get_service_manager()
        # Initialize services if not already done
        if not _service_manager._services:
            _service_manager.initialize_services()
    return _service_manager.vm_service


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting FastAPI web server...")
    port = getattr(settings, "WEB_PORT", 3080)
    logger.info(f"Web interface available at http://localhost:{port}")
    # Initialize service manager on startup
    try:
        get_vm_service()
        logger.info("Service manager initialized successfully")
    except Exception as e:
        logger.warning(f"Service manager initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down FastAPI web server...")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading template: {e}", exc_info=True)
        logger.error(f"Template directory: {TEMPLATES_DIR}")
        logger.error(f"Template file exists: {(TEMPLATES_DIR / 'index.html').exists()}")
        raise HTTPException(status_code=500, detail=f"Template error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "virtualization-mcp-web",
        "version": settings.APP_VERSION,
    }


@app.get("/api/vms")
async def list_vms():
    """List all virtual machines."""
    try:
        from ..tools.vm.vm_tools import list_vms as list_vms_tool

        vms = await list_vms_tool()
        return {"success": True, "data": vms, "count": len(vms)}
    except Exception as e:
        logger.error(f"Error listing VMs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vms/{vm_name}")
async def get_vm_info(vm_name: str):
    """Get detailed information about a VM."""
    try:
        from ..tools.vm.vm_tools import get_vm_info as get_vm_info_tool

        info = await get_vm_info_tool(vm_name)
        if not info:
            raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found")
        return {"success": True, "data": info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting VM info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vms/{vm_name}/start")
async def start_vm(vm_name: str):
    """Start a virtual machine."""
    try:
        from ..tools.vm.vm_tools import start_vm as start_vm_tool

        result = await start_vm_tool(vm_name)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error starting VM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vms/{vm_name}/stop")
async def stop_vm(vm_name: str):
    """Stop a virtual machine."""
    try:
        from ..tools.vm.vm_tools import stop_vm as stop_vm_tool

        result = await stop_vm_tool(vm_name)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error stopping VM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vms")
async def create_vm(request: Request):
    """Create a new virtual machine."""
    try:
        data = await request.json()
        from ..tools.vm.vm_tools import create_vm as create_vm_tool

        result = await create_vm_tool(
            name=data.get("name"),
            ostype=data.get("os_type"),  # Note: function expects 'ostype', not 'os_type'
            memory_mb=data.get("memory_mb", 4096),
            disk_size_gb=data.get("disk_size_gb", 50),
        )
        # Check if result indicates success
        if result.get("status") == "error":
            return {"success": False, "error": result.get("message", "Unknown error"), "data": result}
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error creating VM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/vms/{vm_name}")
async def delete_vm(vm_name: str):
    """Delete a virtual machine."""
    try:
        from ..tools.vm.vm_tools import delete_vm as delete_vm_tool

        result = await delete_vm_tool(vm_name)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error deleting VM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/info")
async def get_system_info():
    """Get system information."""
    try:
        from ..tools.system.system_tools import get_system_info as get_system_info_tool

        info = await get_system_info_tool()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting system info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket support for real-time updates
try:
    import socketio

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    socketio_app = socketio.ASGIApp(sio, app)

    @sio.event
    async def connect(sid, environ):
        """Handle WebSocket connection."""
        logger.info(f"WebSocket client connected: {sid}")
        await sio.emit("status", {"message": "Connected to virtualization-mcp"})

    @sio.event
    async def disconnect(sid):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket client disconnected: {sid}")

    @sio.event
    async def subscribe_vm_status(sid, data):
        """Subscribe to VM status updates."""
        vm_name = data.get("vm_name")
        logger.info(f"Client {sid} subscribed to VM status: {vm_name}")
        # TODO: Implement VM status broadcasting

    # Use socketio app as the main app
    app = socketio_app

except ImportError:
    logger.warning("python-socketio not installed, WebSocket support disabled")
    socketio_app = None

