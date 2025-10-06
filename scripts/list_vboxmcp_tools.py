"""
List all available tools in the virtualization_mcp MCP server.

This script connects to the virtualization_mcp server and lists all available tools
with their descriptions and parameters.
"""

import asyncio
from fastmcp import FastMCP

async def list_virtualization_mcp_tools():
    """List all available tools in the virtualization_mcp MCP server."""
    # Initialize MCP client
    mcp = FastMCP("virtualization_mcp-tool-lister")
    
    try:
        print("Available tools in virtualization_mcp server:")
        print("=" * 80)
        
        # Get the list of tools from the server
        tools = await mcp.call("list_tools", {})
        
        if not tools or not isinstance(tools, list):
            print("No tools found or invalid response format")
            return
            
        # Print each tool with its details
        for tool in tools:
            name = tool.get('name', 'unknown')
            description = tool.get('description', 'No description available')
            params = tool.get('parameters', {})
            
            print(f"\n{name}")
            print("-" * len(name))
            print(f"  {description}")
            
            if params:
                print("\n  Parameters:")
                for param_name, param_info in params.items():
                    param_type = param_info.get('type', 'any')
                    param_desc = param_info.get('description', 'No description')
                    required = param_info.get('required', False)
                    default = param_info.get('default', 'No default')
                    
                    print(f"    - {param_name} ({param_type}{', required' if required else ''})")
                    print(f"      {param_desc}")
                    if default != 'No default':
                        print(f"      Default: {default}")
            
            print("\n" + "=" * 80)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up if needed
        if hasattr(mcp, 'disconnect'):
            await mcp.disconnect()

if __name__ == "__main__":
    asyncio.run(list_virtualization_mcp_tools())
