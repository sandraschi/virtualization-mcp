#!/usr/bin/env python3
"""
VirtualBox MCP Server - FastMCP 2.10.1 Implementation
Austrian dev efficiency: Complete VM management through MCP protocol
"""

import argparse
import logging
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Now import local modules
from virtualization-mcp.vbox.manager import VBoxManager, VBoxManagerError
from virtualization-mcp.vbox.templates import TemplateManager
from virtualization-mcp.vbox.vm_operations import VMOperations
from virtualization-mcp.vbox.snapshots import SnapshotManager
from virtualization-mcp.vbox.networking import NetworkManager

# Set up logging
logger = logging.getLogger('virtualization-mcp')

def setup_logging(debug: bool = False) -> None:
    """Configure logging with optional debug mode."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logging.getLogger('fastmcp').setLevel(logging.WARNING if not debug else logging.DEBUG)

# Dependencies
try:
    from fastmcp import FastMCP
except ImportError as e:
    # print(f"Error: fastmcp package not found: {e}")
    # print("Please install it with: pip install fastmcp")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    logger.warning("python-dotenv not found. Some features may not work as expected.")
    load_dotenv = lambda: None

try:
    import yaml
except ImportError:
    logger.warning("PyYAML not found. Some features may not work as expected.")
    yaml = None

# Import VBox components
try:
    from virtualization-mcp.vbox.manager import VBoxManager, VBoxManagerError
    from virtualization-mcp.vbox.templates import TemplateManager
except ImportError as e:
    logger.error(f"Error importing VBox components: {e}")
    logger.error("Please ensure the virtualization-mcp package is properly installed.")
    traceback.print_exc()
    sys.exit(1)

# Global variables
vbox_manager = None
template_manager = None
mcp = None

def handle_shutdown(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received, cleaning up...")
    if mcp:
        mcp.shutdown()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

logger = logging.getLogger("virtualization-mcp")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server with Austrian efficiency
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "VirtualBox MCP Server 🚀"),
    instructions="""
    Provides comprehensive VirtualBox management through natural language commands.
    Austrian dev efficiency: Working solutions in hours, not days.
    
    Core capabilities:
    • VM lifecycle management (create, start, stop, delete)
    • Template-based rapid deployment (ubuntu-dev, windows-test, etc.)
    • Snapshot management for testing workflows
    • Network configuration and port forwarding
    • Multi-VM environment setup
    
    Templates available: ubuntu-dev, windows-test, minimal-linux, database-server,
    web-server, docker-host, security-test, kubernetes-node, monitoring-stack, jenkins-ci
    
    Example queries:
    - "Create Ubuntu development VM with 4GB RAM"
    - "Take snapshot of test-db before running migrations"
    - "Set up load testing environment with 3 web servers"
    - "Configure port forwarding for SSH access"
    - "Restore VM to clean state and restart"
    """,
    dependencies=[
        "fastmcp>=2.10.0",
        "pyyaml>=6.0.1", 
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0"
    ]
)

# Initialize VirtualBox components
try:
    vbox_manager = VBoxManager(os.getenv("VBOXMANAGE_PATH", "VBoxManage"))
    vm_operations = VMOperations(vbox_manager)
    snapshot_manager = SnapshotManager(vbox_manager)
    network_manager = NetworkManager(vbox_manager)
    template_manager = TemplateManager(Path("config/vm_templates.yaml"))
    
    logger.info("VirtualBox MCP Server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize VirtualBox components: {e}")
    raise


# ============================================================================
# VM LIFECYCLE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def create_vm(name: str, template: str = "ubuntu-dev", 
              memory_mb: Optional[int] = None, 
              disk_gb: Optional[int] = None) -> Dict[str, Any]:
    """
    Create new VM from template with optional overrides.
    
    Args:
        name: VM name (must be unique)
        template: Template name (ubuntu-dev, windows-test, minimal-linux, etc.)
        memory_mb: Override template memory allocation
        disk_gb: Override template disk size
        
    Returns:
        VM creation result with configuration details
    """
    try:
        logger.info(f"Creating VM '{name}' from template '{template}'")
        
        result = vm_operations.create_vm(
            name=name,
            template=template,
            memory_mb=memory_mb,
            disk_gb=disk_gb
        )
        
        return {
            "success": True,
            "vm_name": name,
            "template": template,
            "message": f"✅ VM '{name}' created successfully from template '{template}'",
            "next_steps": [
                f"Start VM: start_vm('{name}')",
                f"Take initial snapshot: create_snapshot('{name}', 'initial')",
                f"Configure networking if needed"
            ],
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to create VM '{name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": name,
            "template": template,
            "message": f"❌ Failed to create VM '{name}': {str(e)}",
            "troubleshooting": [
                "Check if VM name is unique",
                "Verify template exists",
                "Ensure sufficient disk space",
                "Check VirtualBox installation"
            ]
        }


@mcp.tool()
def start_vm(name: str, headless: bool = True) -> Dict[str, Any]:
    """
    Start virtual machine (headless by default for testing).
    
    Args:
        name: VM name to start
        headless: Start without GUI (recommended for automation)
        
    Returns:
        VM start result
    """
    try:
        logger.info(f"Starting VM '{name}' (headless={headless})")
        
        result = vm_operations.start_vm(name, headless=headless)
        
        return {
            "success": True,
            "vm_name": name,
            "mode": "headless" if headless else "gui",
            "message": f"✅ VM '{name}' started successfully",
            "next_steps": [
                "Wait for boot completion",
                "Check VM status with get_vm_info",
                "Configure network access if needed"
            ],
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to start VM '{name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": name,
            "message": f"❌ Failed to start VM '{name}': {str(e)}",
            "troubleshooting": [
                "Check if VM exists",
                "Verify VM is not already running",
                "Check host system resources",
                "Review VM configuration"
            ]
        }


@mcp.tool()
def stop_vm(name: str, force: bool = False) -> Dict[str, Any]:
    """
    Stop VM gracefully or forcefully.
    
    Args:
        name: VM name to stop
        force: Force stop (power off) vs graceful shutdown
        
    Returns:
        VM stop result
    """
    try:
        logger.info(f"Stopping VM '{name}' (force={force})")
        
        result = vm_operations.stop_vm(name, force=force)
        
        return {
            "success": True,
            "vm_name": name,
            "method": "forced" if force else "graceful",
            "message": f"✅ VM '{name}' stopped successfully",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to stop VM '{name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": name,
            "message": f"❌ Failed to stop VM '{name}': {str(e)}"
        }


@mcp.tool()
def delete_vm(name: str, delete_disk: bool = True) -> Dict[str, Any]:
    """
    Delete VM and optionally its disk files.
    
    Args:
        name: VM name to delete
        delete_disk: Also delete VM disk files (recommended)
        
    Returns:
        VM deletion result
    """
    try:
        logger.info(f"Deleting VM '{name}' (delete_disk={delete_disk})")
        
        # Safety check - confirm VM exists and get state
        vm_state = vbox_manager.get_vm_state(name)
        
        result = vm_operations.delete_vm(name, delete_disk=delete_disk)
        
        return {
            "success": True,
            "vm_name": name,
            "disk_deleted": delete_disk,
            "previous_state": vm_state,
            "message": f"✅ VM '{name}' deleted successfully",
            "warning": "This action cannot be undone" if delete_disk else "Disk files preserved",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to delete VM '{name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": name,
            "message": f"❌ Failed to delete VM '{name}': {str(e)}"
        }


@mcp.tool()
def list_vms(state_filter: str = "all") -> Dict[str, Any]:
    """
    List VMs with optional state filtering.
    
    Args:
        state_filter: Filter by state - "all", "running", "stopped", "saved"
        
    Returns:
        List of VMs with their current states
    """
    try:
        logger.info(f"Listing VMs (filter: {state_filter})")
        
        vms = vbox_manager.list_vms(state_filter)
        
        # Enhance with detailed state information
        enhanced_vms = []
        for vm in vms:
            try:
                vm_info = vbox_manager.get_vm_info(vm["name"])
                enhanced_vm = {
                    "name": vm["name"],
                    "uuid": vm["uuid"],
                    "state": vm_info.get("VMState", "unknown"),
                    "memory_mb": vm_info.get("memory", "unknown"),
                    "os_type": vm_info.get("ostype", "unknown"),
                    "created": vm_info.get("CfgFile", "unknown")
                }
                enhanced_vms.append(enhanced_vm)
            except Exception as e:
                logger.warning(f"Failed to get details for VM '{vm['name']}': {e}")
                enhanced_vms.append(vm)
        
        return {
            "success": True,
            "filter": state_filter,
            "count": len(enhanced_vms),
            "vms": enhanced_vms,
            "message": f"✅ Found {len(enhanced_vms)} VMs"
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to list VMs: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to list VMs: {str(e)}"
        }


# ============================================================================
# SNAPSHOT MANAGEMENT TOOLS  
# ============================================================================

@mcp.tool()
def create_snapshot(vm_name: str, snapshot_name: str, 
                   description: str = "") -> Dict[str, Any]:
    """
    Create VM snapshot for testing rollback.
    
    Args:
        vm_name: VM name
        snapshot_name: Snapshot identifier
        description: Optional description
        
    Returns:
        Snapshot creation result
    """
    try:
        logger.info(f"Creating snapshot '{snapshot_name}' for VM '{vm_name}'")
        
        result = snapshot_manager.create_snapshot(vm_name, snapshot_name, description)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"✅ Snapshot '{snapshot_name}' created for VM '{vm_name}'",
            "usage": f"Restore with: restore_snapshot('{vm_name}', '{snapshot_name}')",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to create snapshot: {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"❌ Failed to create snapshot: {str(e)}"
        }


@mcp.tool()
def restore_snapshot(vm_name: str, snapshot_name: str) -> Dict[str, Any]:
    """
    Restore VM to specific snapshot state.
    
    Args:
        vm_name: VM name
        snapshot_name: Snapshot to restore
        
    Returns:
        Snapshot restore result
    """
    try:
        logger.info(f"Restoring VM '{vm_name}' to snapshot '{snapshot_name}'")
        
        result = snapshot_manager.restore_snapshot(vm_name, snapshot_name)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"✅ VM '{vm_name}' restored to snapshot '{snapshot_name}'",
            "note": "VM was stopped for restore operation",
            "next_steps": [f"Start VM: start_vm('{vm_name}')"],
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to restore snapshot: {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"❌ Failed to restore snapshot: {str(e)}"
        }


@mcp.tool()
def delete_snapshot(vm_name: str, snapshot_name: str) -> Dict[str, Any]:
    """
    Delete snapshot to save disk space.
    
    Args:
        vm_name: VM name
        snapshot_name: Snapshot to delete
        
    Returns:
        Snapshot deletion result
    """
    try:
        logger.info(f"Deleting snapshot '{snapshot_name}' for VM '{vm_name}'")
        
        result = snapshot_manager.delete_snapshot(vm_name, snapshot_name)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"✅ Snapshot '{snapshot_name}' deleted",
            "benefit": "Disk space freed",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to delete snapshot: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to delete snapshot: {str(e)}"
        }


@mcp.tool()
def list_snapshots(vm_name: str) -> Dict[str, Any]:
    """
    List all snapshots for a VM.
    
    Args:
        vm_name: VM name
        
    Returns:
        List of snapshots with metadata
    """
    try:
        logger.info(f"Listing snapshots for VM '{vm_name}'")
        
        snapshots = snapshot_manager.list_snapshots(vm_name)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "count": len(snapshots),
            "snapshots": snapshots,
            "message": f"✅ Found {len(snapshots)} snapshots for VM '{vm_name}'"
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to list snapshots: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to list snapshots: {str(e)}"
        }


@mcp.tool()
def rollback_and_restart(vm_name: str, snapshot_name: str) -> Dict[str, Any]:
    """
    Atomic rollback to snapshot and restart VM.
    
    Args:
        vm_name: VM name
        snapshot_name: Snapshot to restore
        
    Returns:
        Combined operation result
    """
    try:
        logger.info(f"Rolling back VM '{vm_name}' to '{snapshot_name}' and restarting")
        
        result = snapshot_manager.rollback_and_restart(vm_name, snapshot_name)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "message": f"✅ VM '{vm_name}' rolled back to '{snapshot_name}' and restarted",
            "operation": "atomic rollback + restart",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed rollback and restart: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed rollback and restart: {str(e)}"
        }


# ============================================================================
# NETWORKING TOOLS
# ============================================================================

@mcp.tool()
def configure_port_forwarding(vm_name: str, host_port: int, 
                             guest_port: int, protocol: str = "tcp") -> Dict[str, Any]:
    """
    Configure port forwarding for VM access.
    
    Args:
        vm_name: VM name
        host_port: Host port number
        guest_port: Guest port number  
        protocol: "tcp" or "udp"
        
    Returns:
        Port forwarding configuration result
    """
    try:
        logger.info(f"Configuring port forwarding for VM '{vm_name}': {host_port}->{guest_port}")
        
        result = network_manager.configure_port_forwarding(
            vm_name, host_port, guest_port, protocol
        )
        
        return {
            "success": True,
            "vm_name": vm_name,
            "host_port": host_port,
            "guest_port": guest_port,
            "protocol": protocol,
            "message": f"✅ Port forwarding configured: localhost:{host_port} -> VM:{guest_port}",
            "access": f"Connect to localhost:{host_port} to reach VM port {guest_port}",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to configure port forwarding: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to configure port forwarding: {str(e)}"
        }


@mcp.tool()
def list_port_forwarding(vm_name: str) -> Dict[str, Any]:
    """
    List all port forwarding rules for VM.
    
    Args:
        vm_name: VM name
        
    Returns:
        List of port forwarding rules
    """
    try:
        logger.info(f"Listing port forwarding for VM '{vm_name}'")
        
        rules = network_manager.list_port_forwarding(vm_name)
        
        return {
            "success": True,
            "vm_name": vm_name,
            "count": len(rules),
            "port_forwards": rules,
            "message": f"✅ Found {len(rules)} port forwarding rules"
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to list port forwarding: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to list port forwarding: {str(e)}"
        }


@mcp.tool()
def get_vm_info(name: str) -> Dict[str, Any]:
    """
    Get detailed VM information and current state.
    
    Args:
        name: VM name
        
    Returns:
        Comprehensive VM information
    """
    try:
        logger.info(f"Getting info for VM '{name}'")
        
        vm_info = vbox_manager.get_vm_info(name)
        vm_state = vbox_manager.get_vm_state(name)
        
        # Get networking info
        port_forwards = network_manager.list_port_forwarding(name)
        
        # Get snapshots
        snapshots = snapshot_manager.list_snapshots(name)
        
        return {
            "success": True,
            "vm_name": name,
            "state": vm_state,
            "memory_mb": vm_info.get("memory", "unknown"),
            "os_type": vm_info.get("ostype", "unknown"),
            "uuid": vm_info.get("UUID", "unknown"),
            "port_forwards": port_forwards,
            "snapshots_count": len(snapshots),
            "snapshots": snapshots[:5],  # Show first 5
            "raw_info": {k: v for k, v in vm_info.items() if k in [
                "memory", "vram", "cpus", "ostype", "boot1", "boot2"
            ]},
            "message": f"✅ VM '{name}' info retrieved"
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to get VM info: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get VM info: {str(e)}"
        }


# ============================================================================
# TEMPLATE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def list_templates() -> Dict[str, Any]:
    """
    List available VM templates with descriptions.
    
    Returns:
        List of available templates
    """
    try:
        logger.info("Listing available VM templates")
        
        templates = template_manager.list_templates()
        
        return {
            "success": True,
            "count": len(templates),
            "templates": templates,
            "message": f"✅ Found {len(templates)} available templates",
            "usage": "Use template name with create_vm(name, template)"
        }
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to list templates: {str(e)}"
        }


@mcp.tool()
def get_template_info(template_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific template.
    
    Args:
        template_name: Template name to query
        
    Returns:
        Detailed template information
    """
    try:
        logger.info(f"Getting info for template '{template_name}'")
        
        template = template_manager.get_template(template_name)
        
        return {
            "success": True,
            "template_name": template_name,
            "configuration": template,
            "memory_mb": template.get("memory_mb"),
            "disk_gb": template.get("disk_gb"),
            "os_type": template.get("os_type"),
            "description": template.get("description"),
            "post_install": template.get("post_install", []),
            "use_cases": template.get("use_cases", []),
            "port_forwards": template.get("port_forwards", []),
            "message": f"✅ Template '{template_name}' info retrieved"
        }
        
    except ValueError as e:
        logger.error(f"Template not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Template '{template_name}' not found",
            "suggestion": "Use list_templates() to see available options"
        }


@mcp.tool()
def search_templates_by_use_case(use_case: str) -> Dict[str, Any]:
    """
    Find templates suitable for specific use case.
    
    Args:
        use_case: Use case description (e.g., "web development", "database")
        
    Returns:
        Matching templates ranked by relevance
    """
    try:
        logger.info(f"Searching templates for use case: '{use_case}'")
        
        matching_templates = template_manager.get_template_for_use_case(use_case)
        
        return {
            "success": True,
            "use_case": use_case,
            "matches": len(matching_templates),
            "templates": matching_templates,
            "message": f"✅ Found {len(matching_templates)} templates for '{use_case}'"
        }
        
    except Exception as e:
        logger.error(f"Failed to search templates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to search templates: {str(e)}"
        }


# ============================================================================
# TESTING WORKFLOW TOOLS
# ============================================================================

@mcp.tool()
def setup_test_environment(env_name: str, vms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create multi-VM test environment from specification.
    
    Args:
        env_name: Environment name
        vms: List of VM specifications with name, template, etc.
        
    Returns:
        Test environment creation result
    """
    try:
        logger.info(f"Setting up test environment '{env_name}' with {len(vms)} VMs")
        
        created_vms = []
        failed_vms = []
        
        for vm_spec in vms:
            try:
                vm_name = f"{env_name}_{vm_spec['name']}"
                
                result = vm_operations.create_vm(
                    name=vm_name,
                    template=vm_spec.get('template', 'ubuntu-dev'),
                    memory_mb=vm_spec.get('memory_mb'),
                    disk_gb=vm_spec.get('disk_gb')
                )
                
                created_vms.append({
                    "name": vm_name,
                    "template": vm_spec.get('template'),
                    "status": "created"
                })
                
                # Start VM if requested
                if vm_spec.get('auto_start', False):
                    vm_operations.start_vm(vm_name, headless=True)
                    created_vms[-1]["status"] = "running"
                    
            except Exception as e:
                logger.error(f"Failed to create VM {vm_spec['name']}: {e}")
                failed_vms.append({
                    "name": vm_spec['name'],
                    "error": str(e)
                })
        
        return {
            "success": len(failed_vms) == 0,
            "environment_name": env_name,
            "created_vms": created_vms,
            "failed_vms": failed_vms,
            "total_requested": len(vms),
            "total_created": len(created_vms),
            "message": f"✅ Test environment '{env_name}' created with {len(created_vms)}/{len(vms)} VMs"
        }
        
    except Exception as e:
        logger.error(f"Failed to setup test environment: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to setup test environment: {str(e)}"
        }


@mcp.tool()
def clone_vm(source: str, target: str, linked: bool = True) -> Dict[str, Any]:
    """
    Clone VM for testing (linked clones save space).
    
    Args:
        source: Source VM name
        target: Target VM name
        linked: Create linked clone (saves disk space)
        
    Returns:
        VM clone result
    """
    try:
        logger.info(f"Cloning VM '{source}' to '{target}' (linked={linked})")
        
        result = snapshot_manager.clone_vm(source, target, linked=linked)
        
        return {
            "success": True,
            "source_vm": source,
            "target_vm": target,
            "linked_clone": linked,
            "message": f"✅ VM '{source}' cloned to '{target}' successfully",
            "space_saving": "High (linked clone)" if linked else "None (full clone)",
            "details": result
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to clone VM: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to clone VM: {str(e)}"
        }


# ============================================================================
# MONITORING AND METRICS TOOLS
# ============================================================================

@mcp.tool()
def get_vm_metrics(name: str) -> Dict[str, Any]:
    """
    Get VM resource usage metrics.
    
    Args:
        name: VM name
        
    Returns:
        VM performance metrics
    """
    try:
        logger.info(f"Getting metrics for VM '{name}'")
        
        vm_info = vbox_manager.get_vm_info(name)
        vm_state = vbox_manager.get_vm_state(name)
        
        # Basic metrics from VM info
        metrics = {
            "vm_name": name,
            "state": vm_state,
            "memory_mb": vm_info.get("memory", 0),
            "cpu_count": vm_info.get("cpus", 0),
            "vram_mb": vm_info.get("vram", 0)
        }
        
        # Add runtime metrics if VM is running
        if vm_state == "running":
            try:
                # Try to get guest metrics (requires Guest Additions)
                ip_result = network_manager.get_vm_ip_address(name)
                if ip_result.get("success"):
                    metrics["ip_address"] = ip_result.get("ip_address")
            except:
                pass
        
        return {
            "success": True,
            "vm_name": name,
            "metrics": metrics,
            "message": f"✅ Metrics retrieved for VM '{name}'"
        }
        
    except VBoxManagerError as e:
        logger.error(f"Failed to get VM metrics: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get VM metrics: {str(e)}"
        }


@mcp.tool()
def get_host_status() -> Dict[str, Any]:
    """
    Get VirtualBox host system status and available resources.
    
    Returns:
        Host system status
    """
    try:
        logger.info("Getting VirtualBox host status")
        
        host_info = vbox_manager.get_host_info()
        
        # Count VMs by state
        all_vms = vbox_manager.list_vms("all")
        running_vms = vbox_manager.list_vms("running")
        
        return {
            "success": True,
            "host_info": host_info,
            "vm_summary": {
                "total_vms": len(all_vms),
                "running_vms": len(running_vms),
                "stopped_vms": len(all_vms) - len(running_vms)
            },
            "server_info": {
                "mcp_server": "VirtualBox MCP",
                "version": "1.0.0",
                "uptime": "Available"
            },
            "message": "✅ Host status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get host status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get host status: {str(e)}"
        }


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
def validate_vm_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate VM configuration before creation.
    
    Args:
        config: VM configuration to validate
        
    Returns:
        Validation result with suggestions
    """
    try:
        logger.info("Validating VM configuration")
        
        issues = []
        warnings = []
        
        # Validate required fields
        required_fields = ["name", "template"]
        for field in required_fields:
            if field not in config or not config[field]:
                issues.append(f"Missing required field: {field}")
        
        # Validate VM name
        vm_name = config.get("name", "")
        if vm_name and not vbox_manager.validate_vm_name(vm_name):
            issues.append(f"Invalid VM name: '{vm_name}'")
        
        if vm_name and vbox_manager.vm_exists(vm_name):
            issues.append(f"VM '{vm_name}' already exists")
        
        # Validate template
        template_name = config.get("template")
        if template_name:
            try:
                template_manager.get_template(template_name)
            except ValueError:
                issues.append(f"Template '{template_name}' not found")
        
        # Validate memory
        memory_mb = config.get("memory_mb")
        if memory_mb and (memory_mb < 128 or memory_mb > 32768):
            warnings.append(f"Memory {memory_mb}MB outside recommended range (128-32768)")
        
        # Validate disk
        disk_gb = config.get("disk_gb")
        if disk_gb and (disk_gb < 1 or disk_gb > 1000):
            warnings.append(f"Disk {disk_gb}GB outside recommended range (1-1000)")
        
        is_valid = len(issues) == 0
        
        return {
            "success": True,
            "valid": is_valid,
            "issues": issues,
            "warnings": warnings,
            "message": "✅ Configuration valid" if is_valid else f"❌ {len(issues)} validation issues found"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to validate configuration: {str(e)}"
        }


# ============================================================================
# SERVER STARTUP AND CONFIGURATION
# ============================================================================

def main(debug: bool = False) -> None:
    """
    Main server startup with Austrian efficiency
    
    Args:
        debug: Enable debug logging and additional diagnostics
    """
    global vbox_manager, template_manager, mcp
    
    try:
        # Set up logging first
        setup_logging(debug=debug)
        logger.info("🚀 Starting VirtualBox MCP Server...")
        logger.debug("Debug mode enabled") if debug else None
        
        # Log environment info
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Working directory: {os.getcwd()}")
        logger.debug(f"Python path: {sys.path}")
        
        try:
            # Initialize VirtualBox manager
            logger.debug("Initializing VirtualBox manager...")
            vbox_manager = VBoxManager(os.getenv("VBOXMANAGE_PATH", "VBoxManage"))
            
            # Initialize template manager with absolute path
            templates_path = project_root / "config" / "vm_templates.yaml"
            logger.debug(f"Using templates path: {templates_path}")
            template_manager = TemplateManager(templates_path=templates_path)
            
            # Initialize FastMCP server
            logger.debug("Initializing FastMCP server...")
            mcp = FastMCP(
                "VirtualBox MCP Server",
                version="1.0.0",
                description="VirtualBox management through MCP protocol"
            )
            
            # Register all tools with the MCP server
            tools = [
                create_vm, start_vm, stop_vm, delete_vm, list_vms,
                create_snapshot, restore_snapshot, delete_snapshot,
                list_snapshots, rollback_and_restart, configure_port_forwarding,
                list_port_forwarding, get_vm_info, list_templates,
                get_template_info, search_templates_by_use_case,
                setup_test_environment, clone_vm, get_vm_metrics,
                get_host_status, validate_vm_configuration
            ]
            
            for tool in tools:
                try:
                    mcp.tool(tool)
                    logger.debug(f"Registered tool: {tool.__name__}")
                except Exception as e:
                    logger.error(f"Failed to register tool {tool.__name__}: {e}")
                    if debug:
                        logger.debug(traceback.format_exc())
            
            # Validate VirtualBox installation
            logger.info("Validating VirtualBox installation...")
            try:
                host_info = vbox_manager.get_host_info()
                logger.info(f"VirtualBox host ready: {host_info.get('Host processor', 'Unknown')}")
                logger.debug(f"Host info: {host_info}")
            except Exception as e:
                logger.error(f"Failed to get VirtualBox host info: {e}")
                if debug:
                    logger.debug(traceback.format_exc())
                raise
            
            # Load templates
            logger.info("Loading VM templates...")
            try:
                templates = template_manager.list_templates()
                logger.info(f"Loaded {len(templates)} VM templates")
                if debug:
                    logger.debug(f"Available templates: {[t.get('name') for t in templates]}")
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
                if debug:
                    logger.debug(traceback.format_exc())
                templates = []
            
            # Server ready
            logger.info("✅ VirtualBox MCP Server ready!")
            logger.info("Austrian efficiency: VM management in hours, not days")
            if templates:
                logger.info("Available templates: " + ", ".join([t.get('name', 'unnamed') for t in templates[:5]]))
                if len(templates) > 5:
                    logger.info(f"... and {len(templates) - 5} more")
            
            # Run server
            logger.info("Starting MCP server...")
            mcp.run()
            
        except VBoxManagerError as e:
            logger.error(f"VirtualBox error: {e}")
            if debug:
                logger.debug(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(f"Unexpected error during server initialization: {e}")
            if debug:
                logger.debug(traceback.format_exc())
            raise
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if debug:
            logger.debug(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")
        raise


if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='VirtualBox MCP Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Parse arguments and run main with debug flag
    args = parser.parse_args()
    
    try:
        main(debug=args.debug)
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        if args.debug:
            logger.critical(traceback.format_exc())
        sys.exit(1)




