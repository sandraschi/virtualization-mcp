"""
List all available VMs in the virtualization_mcp server.

This script demonstrates how to list VMs using the FastMCP client.
"""

import asyncio
from fastmcp import FastMCP

async def list_vms():
    """List all available VMs in the virtualization_mcp server."""
    # Initialize MCP client
    mcp = FastMCP("virtualization_mcp-vm-lister")
    
    try:
        print("Connecting to virtualization_mcp server...")
        
        # List VMs using the standard MCP method
        vms = mcp.list_vms()
        
        if not vms or not isinstance(vms, dict) or 'vms' not in vms:
            print("No VMs found or invalid response format")
            print(f"Response: {vms}")
            return
            
        print("\nAvailable VMs:")
        print("=" * 80)
        
        for vm in vms.get('vms', []):
            name = vm.get('name', 'Unknown')
            state = vm.get('state', 'unknown')
            print(f"- {name} ({state})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up if needed
        if hasattr(mcp, 'disconnect'):
            await mcp.disconnect()

if __name__ == "__main__":
    asyncio.run(list_vms())



