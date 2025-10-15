"""
List all available MCP tools via stdio interface.

This script connects to the MCP server and lists all available tools
with their descriptions and categories.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP


async def list_mcp_tools():
    """List all available MCP tools."""
    # Initialize MCP client
    mcp = FastMCP("virtualization_mcp-tool-lister", version="1.0.0")

    try:
        # Get the list of VMs as a way to test the connection
        print("Connecting to virtualization_mcp server...")
        response = mcp.call("list_vms", {})

        if not response or not isinstance(response, dict) or "vms" not in response:
            print("No VMs found or invalid response format")
            print(f"Response: {response}")
            return

        print(f"\n{'=' * 80}")
        print(f"{'MCP Tools':^80}")
        print(f"{'=' * 80}")

        # Group tools by category
        tools_by_category = {}
        for tool in response:
            categories = tool.get("categories", ["uncategorized"])
            for category in categories:
                if category not in tools_by_category:
                    tools_by_category[category] = []
                tools_by_category[category].append(tool)

        # Print tools by category
        for category, tools in sorted(tools_by_category.items()):
            print(f"\n{category.upper()}:")
            print("-" * 80)

            for tool in sorted(tools, key=lambda x: x["name"]):
                name = tool["name"]
                desc = tool.get("description", "No description available")
                params = ", ".join([f"{p}" for p in tool.get("parameters", {}).keys()])

                print(f"{name}({params})")
                print(f"  {desc}")

                # Show endpoint if available (for HTTP)
                if "endpoint" in tool:
                    print(f"  Endpoint: {tool['method'].upper()} {tool['endpoint']}")

                print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(list_mcp_tools())
