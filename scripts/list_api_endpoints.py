"""
List all available API endpoints in the virtualization_mcp server.

This script connects to the virtualization_mcp server and lists all available API endpoints.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional

async def list_api_endpoints(server_url: str = "http://localhost:8000") -> None:
    """List all available API endpoints in the virtualization_mcp server.
    
    Args:
        server_url: Base URL of the virtualization_mcp server
    """
    # Known API endpoints to check
    endpoints = [
        "/tools",
        "/endpoints",
        "/api",
        "/v1/tools",
        "/v1/endpoints",
        "/v1/api"
    ]
    
    print(f"Checking for API endpoints at {server_url}...\n")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = f"{server_url.rstrip('/')}{endpoint}"
            try:
                print(f"Trying endpoint: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\nFound API endpoint: {endpoint}")
                        print("-" * (len(endpoint) + 20))
                        print(json.dumps(data, indent=2))
                        print("\n" + "=" * 80 + "\n")
                    else:
                        print(f"  - Status: {response.status}")
            except Exception as e:
                print(f"  - Error: {str(e)}")
            
            # Add a small delay between requests
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='List available API endpoints in the virtualization_mcp server')
    parser.add_argument('--server', type=str, default="http://localhost:8000",
                       help='Base URL of the virtualization_mcp server')
    
    args = parser.parse_args()
    
    asyncio.run(list_api_endpoints(args.server))
