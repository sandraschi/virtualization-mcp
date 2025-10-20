"""
Example: Windows Sandbox with Folder Mapping

This example demonstrates how to create a Windows Sandbox with mapped folders
after the folder mapping fix.
"""

import asyncio
from pathlib import Path

from virtualization_mcp.plugins.sandbox import MappedFolder, SandboxConfig, WindowsSandboxHelper


async def example_basic_mapping():
    """Example 1: Basic folder mapping."""
    print("Example 1: Basic folder mapping")
    print("-" * 50)

    # Create a sandbox with a single mapped folder
    config = SandboxConfig(
        name="basic-sandbox",
        memory_mb=2048,
        mapped_folders=[
            MappedFolder(
                host_path=str(Path.home() / "Documents"),
                readonly=False
            )
        ]
    )

    helper = WindowsSandboxHelper()
    xml = helper._generate_wsx_config(config)
    print("Generated WSX configuration:")
    print(xml)
    print()


async def example_multiple_folders():
    """Example 2: Multiple folders with different settings."""
    print("Example 2: Multiple folders")
    print("-" * 50)

    config = SandboxConfig(
        name="multi-folder-sandbox",
        memory_mb=4096,
        vgpu=True,
        networking=True,
        mapped_folders=[
            # Map Documents as read-write
            MappedFolder(
                host_path=str(Path.home() / "Documents"),
                sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Documents",
                readonly=False
            ),
            # Map Downloads as read-only
            MappedFolder(
                host_path=str(Path.home() / "Downloads"),
                sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Downloads",
                readonly=True
            )
        ]
    )

    helper = WindowsSandboxHelper()
    xml = helper._generate_wsx_config(config)
    print("Generated WSX configuration:")
    print(xml)
    print()


async def example_with_commands():
    """Example 3: Folders with startup commands."""
    print("Example 3: Folders with startup commands")
    print("-" * 50)

    config = SandboxConfig(
        name="dev-sandbox",
        memory_mb=4096,
        vgpu=True,
        networking=True,
        mapped_folders=[
            MappedFolder(
                host_path=str(Path.home() / "Documents"),
                sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Documents",
                readonly=False
            )
        ],
        logon_commands=[
            "echo Welcome to Development Sandbox!",
            'cd C:\\Users\\WDAGUtilityAccount\\Desktop\\Documents',
            "dir",
            'powershell -Command "Write-Host \'Setup complete!\' -ForegroundColor Green"'
        ]
    )

    helper = WindowsSandboxHelper()
    xml = helper._generate_wsx_config(config)
    print("Generated WSX configuration:")
    print(xml)
    print()


async def example_isolated_test_env():
    """Example 4: Isolated testing environment (example only - folders don't exist)."""
    print("Example 4: Isolated testing environment")
    print("-" * 50)
    print("NOTE: This example would fail validation because folders don't exist.")
    print("      In real use, create the folders first or use existing paths.")
    print()
    print("Example configuration would be:")
    print("""
config = SandboxConfig(
    name="test-env",
    memory_mb=2048,
    vgpu=False,
    networking=True,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\\\TestData",
            sandbox_path="C:\\\\Users\\\\WDAGUtilityAccount\\\\Desktop\\\\TestData",
            readonly=True
        ),
        MappedFolder(
            host_path="C:\\\\TestResults",
            sandbox_path="C:\\\\Users\\\\WDAGUtilityAccount\\\\Desktop\\\\Results",
            readonly=False
        )
    ],
    logon_commands=[
        'echo Running tests...',
        'cd C:\\\\Users\\\\WDAGUtilityAccount\\\\Desktop\\\\TestData',
        ':: Run your tests here',
        'echo Tests complete!'
    ]
)
""")
    print()


async def example_xml_escaping():
    """Example 5: Special characters are properly escaped."""
    print("Example 5: XML special character escaping")
    print("-" * 50)

    config = SandboxConfig(
        name="special-chars",
        memory_mb=2048,
        logon_commands=[
            'echo "Hello & Goodbye"',
            'dir "C:\\Program Files" > output.txt',
            'type output.txt | findstr /i "important"'
        ]
    )

    helper = WindowsSandboxHelper()
    xml = helper._generate_wsx_config(config)
    print("Generated WSX configuration (note the XML escaping):")
    print(xml)
    print()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Windows Sandbox Folder Mapping Examples")
    print("=" * 60)
    print()

    # Note: These examples generate XML but don't actually create sandboxes
    # To create a sandbox, you would use the create_windows_sandbox tool

    await example_basic_mapping()
    await example_multiple_folders()
    await example_with_commands()
    await example_isolated_test_env()  # Just prints info, doesn't actually create
    await example_xml_escaping()

    print("=" * 60)
    print("Examples complete!")
    print()
    print("To use in Claude, try commands like:")
    print('  "Create a Windows Sandbox with my Documents folder mapped"')
    print('  "Create a sandbox for testing with test data as read-only"')
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

