"""
List all available tools in the MCP server.

This script demonstrates how to list all available tools in the MCP server
using the FastMCP client.
"""

import asyncio
import inspect
from fastmcp import FastMCP

async def list_available_tools():
    """List all available tools in the MCP server."""
    # Initialize MCP client
    mcp = FastMCP("virtualization_mcp-tool-lister")
    
    try:
        print("Available tools in virtualization_mcp server:")
        print("=" * 80)
        
        # Get all methods of the FastMCP instance
        for name, method in inspect.getmembers(mcp, callable):
            # Skip private methods and standard object methods
            if name.startswith('_') or name in dir(object):
                continue
                
            # Get the docstring if available
            doc = inspect.getdoc(method) or "No documentation available"
            
            # Print the method name and first line of docstring
            print(f"\n{name}()")
            print("-" * (len(name) + 2))
            print(f"  {doc.split('\n')[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up if needed
        if hasattr(mcp, 'disconnect'):
            await mcp.disconnect()

if __name__ == "__main__":
    asyncio.run(list_available_tools())



