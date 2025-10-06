"""
virtualization-mcp Help System

Provides comprehensive help and examples for all virtualization-mcp functionality.
This module includes the HelpTool class that handles all help-related operations,
including command documentation, examples, and usage patterns.
"""
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import textwrap
import inspect
from pathlib import Path
from datetime import datetime

# Version information
__version__ = "1.0.0"

class HelpCategory(str, Enum):
    """Categories for organizing help topics.
    
    Attributes:
        VM_MANAGEMENT: Operations related to VM lifecycle and management
        STORAGE: Storage management and configuration
        NETWORK: Network setup and configuration
        SNAPSHOTS: Snapshot management operations
        SYSTEM: System information and utilities
        PLUGINS: Plugin management and development
        SECURITY: Security and access control
        MONITORING: Monitoring and logging
        TROUBLESHOOTING: Common issues and solutions
    """
    VM_MANAGEMENT = "Virtual Machine Management"
    STORAGE = "Storage Management"
    NETWORK = "Network Configuration"
    SNAPSHOTS = "Snapshots"
    SYSTEM = "System Information"
    PLUGINS = "Plugins"
    SECURITY = "Security"
    MONITORING = "Monitoring"
    TROUBLESHOOTING = "Troubleshooting"

class HelpTool:
    """
    Main help system for virtualization-mcp that provides comprehensive documentation and examples.
    
    This class handles all help-related functionality including command documentation,
    examples, and usage patterns. It integrates with the MCP system to provide
    contextual help for all registered tools.
    
    Attributes:
        mcp: Reference to the MCP instance
        _help_topics: Dictionary of all help topics
        _last_updated: Timestamp of last help content update
    """
    
    def __init__(self, mcp):
        """Initialize the HelpTool with MCP instance.
        
        Args:
            mcp: The MCP instance to register help tools with
        """
        self.mcp = mcp
        self._help_topics: Dict[str, Dict[str, Any]] = {}
        self._last_updated: Optional[datetime] = None
        self._initialize_help_content()
        self._register_help_tools()
    
    def _initialize_help_content(self) -> None:
        """Initialize the help content with default topics and examples."""
        self._help_topics = {
            "vm_management": {
                "name": "Virtual Machine Management",
                "category": HelpCategory.VM_MANAGEMENT,
                "description": "Manage virtual machine lifecycle and operations",
                "commands": [
                    {
                        "name": "create_vm",
                        "syntax": "create_vm(name: str, template: Optional[str] = None, **options)",
                        "description": "Create a new virtual machine",
                        "examples": [
                            "create_vm('my_vm', template='ubuntu-2204')",
                            "create_vm('dev_env', memory_gb=8, cpu_count=4, os_type='linux')"
                        ]
                    },
                    # Additional commands...
                ]
            },
            # Additional topics...
        }
        self._last_updated = datetime.utcnow()
    
    def _register_help_tools(self) -> None:
        """Register all help-related tools with MCP."""
        
        @self.mcp.tool(
            name="get_help",
            description="Get help with virtualization-mcp commands and features",
            endpoint="/help",
            category=HelpCategory.SYSTEM
        )
        async def get_help(
            topic: Optional[str] = None,
            category: Optional[HelpCategory] = None,
            show_examples: bool = True,
            format: str = "text"
        ) -> Dict[str, Union[str, List[Dict]]]:
            """
            Get help for virtualization-mcp commands and features.
            
            This function provides detailed documentation and examples for virtualization-mcp commands.
            It can filter by topic or category and supports multiple output formats.
            
            Args:
                topic: Specific command or topic to get help for
                category: Filter by category (vm, storage, network, etc.)
                show_examples: Whether to include usage examples (default: True)
                format: Output format ('text' or 'json')
                
            Returns:
                Dictionary containing help information with the following structure:
                {
                    'topic': str,           # The requested topic
                    'description': str,     # Description of the topic
                    'commands': List[Dict], # List of commands with details
                    'examples': List[str],  # Usage examples
                    'last_updated': str     # Timestamp of last update
                }
                
            Example:
                # Get general help
                await get_help()
                
                # Get help for VM management
                await get_help(category="vm")
                
                # Get help for a specific command
                await get_help(topic="create_vm")
            """
            if topic:
                return await self._get_topic_help(topic, show_examples)
            elif category:
                return await self._get_category_help(category, show_examples)
            else:
                return await self._get_general_help()
    
    async def _get_general_help(self) -> Dict[str, Union[str, List[Dict]]]:
        """Return general help information."""
        return {
            "title": "virtualization-mcp Help System",
            "description": "Welcome to virtualization-mcp - A powerful VirtualBox management platform.\n\n"
                         "Use the following commands to explore functionality:",
            "categories": [
                {
                    "name": "Virtual Machine Management",
                    "description": "Create, start, stop, and manage VMs",
                    "commands": ["create_vm", "start_vm", "stop_vm", "delete_vm", "list_vms"]
                },
                {
                    "name": "Storage Management",
                    "description": "Manage virtual disks and storage controllers",
                    "commands": ["create_disk", "attach_disk", "list_disks", "resize_disk"]
                },
                {
                    "name": "Network Configuration",
                    "description": "Configure virtual networks and adapters",
                    "commands": ["configure_network_adapter", "list_networks"]
                },
                {
                    "name": "Snapshots",
                    "description": "Manage VM snapshots",
                    "commands": ["create_snapshot", "restore_snapshot", "list_snapshots"]
                },
                {
                    "name": "System Information",
                    "description": "Get system and VM information",
                    "commands": ["get_system_info", "get_vm_info"]
                },
                {
                    "name": "Help",
                    "description": "Get help with commands",
                    "commands": ["get_help", "list_commands"]
                }
            ],
            "usage": [
                "# List all available commands",
                "await list_commands()",
                "",
                "# Get help for a specific command",
                "await get_help(topic='create_vm')",
                "",
                "# Get help for a category",
                "await get_help(category='vm')",
                "",
                "# Get help with examples",
                "await get_help(topic='start_vm', show_examples=True)"
            ]
        }
    
    async def _get_topic_help(self, topic: str, show_examples: bool) -> Dict[str, str]:
        """Get help for a specific topic or command."""
        # This would be populated with actual command documentation
        help_data = {
            "create_vm": {
                "description": "Create a new virtual machine",
                "usage": "create_vm(name: str, memory_mb: int = 2048, cpu_count: int = 2, disk_size_gb: int = 20)",
                "parameters": [
                    {"name": "name", "type": "str", "required": True, "description": "Name for the new VM"},
                    {"name": "memory_mb", "type": "int", "default": 2048, "description": "Memory in MB"},
                    {"name": "cpu_count", "type": "int", "default": 2, "description": "Number of CPUs"},
                    {"name": "disk_size_gb", "type": "int", "default": 20, "description": "Disk size in GB"}
                ],
                "returns": "Dict with VM creation status",
                "examples": [
                    "# Create a basic VM",
                    "result = await create_vm('my_vm')",
                    "",
                    "# Create a VM with custom resources",
                    "result = await create_vm('dev_vm', memory_mb=4096, cpu_count=4, disk_size_gb=50)"
                ]
            },
            # Add more command documentation as needed
        }
        
        if topic not in help_data:
            return {"error": f"No help available for topic: {topic}"}
        
        help_info = help_data[topic].copy()
        
        if not show_examples and "examples" in help_info:
            del help_info["examples"]
            
        return help_info
    
    async def _get_category_help(self, category: HelpCategory, show_examples: bool) -> Dict:
        """Get help for a specific category."""
        # This would be populated with actual category information
        categories = {
            HelpCategory.VM_MANAGEMENT: {
                "description": "Manage virtual machines (create, start, stop, delete, etc.)",
                "commands": [
                    {"name": "create_vm", "description": "Create a new VM"},
                    {"name": "start_vm", "description": "Start a VM"},
                    {"name": "stop_vm", "description": "Stop a running VM"},
                    {"name": "delete_vm", "description": "Delete a VM"},
                    {"name": "list_vms", "description": "List all VMs"},
                    {"name": "get_vm_info", "description": "Get detailed VM information"}
                ]
            },
            # Add other categories as needed
        }
        
        if category not in categories:
            return {"error": f"Unknown category: {category}"}
            
        return categories[category]

def help_command():
    """
    Provides help and documentation for all available commands.
    
    Returns:
        dict: A dictionary containing help information for all registered commands.
    """
    help_tool = HelpTool()
    return {
        "status": "success",
        "commands": help_tool.get_all_commands_help(),
        "examples": help_tool.get_common_examples(),
        "version": __version__,
        "timestamp": datetime.utcnow().isoformat()
    }

# Example usage:
# help_tool = HelpTool(mcp_instance)
# help_tool.register_help_tools()



