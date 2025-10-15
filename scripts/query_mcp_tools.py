"""
Query the MCP server for available tools.

This script connects to the MCP server and lists all available tools.
"""

import asyncio

import aiohttp


async def query_mcp_tools(server_url: str = "http://localhost:8000") -> None:
    """Query the MCP server for available tools.

    Args:
        server_url: Base URL of the MCP server
    """
    tools_endpoint = f"{server_url}/tools"

    try:
        async with aiohttp.ClientSession() as session:
            print(f"Querying MCP server at {tools_endpoint}...")
            async with session.get(tools_endpoint) as response:
                if response.status == 200:
                    tools = await response.json()
                    print("\nAvailable MCP Tools:")
                    print("=" * 50)

                    if not tools or not isinstance(tools, list):
                        print("No tools found or invalid response format")
                        return

                    for tool in tools:
                        name = tool.get("name", "unknown")
                        description = tool.get("description", "No description available")

                        print(f"\n{name}")
                        print("-" * len(name))
                        print(f"  {description}")

                        if "parameters" in tool:
                            print("\n  Parameters:")
                            for param_name, param_info in tool["parameters"].items():
                                param_type = param_info.get("type", "any")
                                param_desc = param_info.get("description", "No description")
                                required = param_info.get("required", False)

                                print(
                                    f"    - {param_name} ({param_type}{', required' if required else ''})"
                                )
                                print(f"      {param_desc}")

                        print("\n" + "=" * 50)
                else:
                    print(f"Error: Server returned status code {response.status}")
                    print(await response.text())

    except Exception as e:
        print(f"Error querying MCP server: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query MCP server for available tools")
    parser.add_argument(
        "--server", type=str, default="http://localhost:8000", help="Base URL of the MCP server"
    )

    args = parser.parse_args()

    asyncio.run(query_mcp_tools(args.server))
