"""
Tests for Windows Sandbox folder mapping functionality.
"""

import tempfile
from pathlib import Path

import pytest

from virtualization_mcp.plugins.sandbox.manager import (
    MappedFolder,
    SandboxConfig,
    WindowsSandboxHelper,
)


def test_mapped_folder_validation():
    """Test MappedFolder validation."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Valid folder
        folder = MappedFolder(host_path=tmpdir)
        assert folder.host_path == str(Path(tmpdir).resolve())
        assert folder.read_only is False
        assert folder.sandbox_path == ""

        # With all options
        folder = MappedFolder(
            host_path=tmpdir,
            sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Shared",
            read_only=True,
        )
        assert folder.read_only is True
        assert folder.sandbox_path == "C:\\Users\\WDAGUtilityAccount\\Desktop\\Shared"


def test_mapped_folder_invalid_path():
    """Test that invalid paths are rejected."""
    with pytest.raises(ValueError, match="Host path does not exist"):
        MappedFolder(host_path="C:\\NonExistentPath123456")


def test_mapped_folder_relative_path():
    """Test that relative paths are rejected."""
    # Relative paths will fail the "exists" check first, which is also correct
    with pytest.raises(ValueError, match="Host path must be absolute"):
        MappedFolder(host_path="relative/path")


def test_sandbox_config_with_folders():
    """Test SandboxConfig with mapped folders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SandboxConfig(
            name="test-sandbox",
            memory_mb=2048,
            mapped_folders=[
                MappedFolder(host_path=tmpdir, read_only=False),
                MappedFolder(
                    host_path=tmpdir,
                    sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Work",
                    read_only=True,
                ),
            ],
            logon_commands=["echo Hello", "dir"],
        )

        assert config.name == "test-sandbox"
        assert config.memory_mb == 2048
        assert len(config.mapped_folders) == 2
        assert len(config.logon_commands) == 2


def test_wsx_xml_generation_basic():
    """Test basic WSX XML generation."""
    helper = WindowsSandboxHelper()

    config = SandboxConfig(
        name="test-sandbox", memory_mb=2048, vgpu=True, networking=True
    )

    xml = helper._generate_wsx_config(config)

    # Check basic structure
    assert "<Configuration>" in xml
    assert "</Configuration>" in xml
    assert "<VGpu>Enable</VGpu>" in xml
    assert "<Networking>Enable</Networking>" in xml
    assert "<MemoryInMB>2048</MemoryInMB>" in xml


def test_wsx_xml_generation_with_folders():
    """Test WSX XML generation with mapped folders."""
    helper = WindowsSandboxHelper()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = SandboxConfig(
            name="test-sandbox",
            memory_mb=2048,
            mapped_folders=[
                MappedFolder(host_path=tmpdir, read_only=False),
                MappedFolder(
                    host_path=tmpdir,
                    sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Shared",
                    read_only=True,
                ),
            ],
        )

        xml = helper._generate_wsx_config(config)

        # Check MappedFolders section
        assert "<MappedFolders>" in xml
        assert "</MappedFolders>" in xml
        assert "<MappedFolder>" in xml
        assert "<HostFolder>" in xml
        assert "<ReadOnly>false</ReadOnly>" in xml
        assert "<ReadOnly>true</ReadOnly>" in xml
        assert "<SandboxFolder>C:\\Users\\WDAGUtilityAccount\\Desktop\\Shared</SandboxFolder>" in xml


def test_wsx_xml_generation_with_commands():
    """Test WSX XML generation with logon commands."""
    helper = WindowsSandboxHelper()

    config = SandboxConfig(
        name="test-sandbox",
        memory_mb=2048,
        logon_commands=[
            "echo Hello World",
            "powershell -Command Get-Date",
            'dir "C:\\Program Files"',
        ],
    )

    xml = helper._generate_wsx_config(config)

    # Check LogonCommand sections - each command gets its own block
    assert xml.count("<LogonCommand>") == 3
    assert xml.count("</LogonCommand>") == 3
    assert "<Command>echo Hello World</Command>" in xml
    assert "<Command>powershell -Command Get-Date</Command>" in xml


def test_wsx_xml_generation_escaping():
    """Test that special XML characters are properly escaped."""
    helper = WindowsSandboxHelper()

    config = SandboxConfig(
        name="test-sandbox",
        memory_mb=2048,
        logon_commands=[
            'echo "Hello & Goodbye" < input.txt > output.txt',
        ],
    )

    xml = helper._generate_wsx_config(config)

    # Check that special characters are escaped
    assert "&amp;" in xml  # & should be escaped
    assert "&lt;" in xml  # < should be escaped
    assert "&gt;" in xml  # > should be escaped
    # Note: saxutils.escape() doesn't escape quotes by default


def test_wsx_xml_generation_complete():
    """Test complete WSX XML generation with all features."""
    helper = WindowsSandboxHelper()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = SandboxConfig(
            name="complete-sandbox",
            memory_mb=4096,
            vgpu=False,
            networking=False,
            mapped_folders=[
                MappedFolder(host_path=tmpdir, read_only=True),
            ],
            logon_commands=["echo Setup complete"],
        )

        xml = helper._generate_wsx_config(config)

        # Verify all sections are present and correct
        assert "<Configuration>" in xml
        assert "<VGpu>Disable</VGpu>" in xml
        assert "<Networking>Disable</Networking>" in xml
        assert "<MemoryInMB>4096</MemoryInMB>" in xml
        assert "<MappedFolders>" in xml
        assert "<MappedFolder>" in xml
        assert f"<HostFolder>{tmpdir}</HostFolder>" in xml or f"<HostFolder>{Path(tmpdir).resolve()}</HostFolder>" in xml
        assert "<ReadOnly>true</ReadOnly>" in xml
        assert "<LogonCommand>" in xml
        assert "<Command>echo Setup complete</Command>" in xml
        assert "</Configuration>" in xml


def test_sandbox_config_validation():
    """Test SandboxConfig validation."""
    # Valid config
    config = SandboxConfig(name="test", memory_mb=2048)
    assert config.name == "test"

    # Empty name should be rejected
    with pytest.raises(ValueError, match="Name cannot be empty"):
        SandboxConfig(name="", memory_mb=2048)

    # Whitespace-only name should be rejected
    with pytest.raises(ValueError, match="Name cannot be empty"):
        SandboxConfig(name="   ", memory_mb=2048)

    # Name should be stripped
    config = SandboxConfig(name="  test  ", memory_mb=2048)
    assert config.name == "test"


def test_memory_validation():
    """Test memory validation."""
    # Valid memory values
    SandboxConfig(name="test", memory_mb=1024)  # Minimum
    SandboxConfig(name="test", memory_mb=16384)  # Middle
    SandboxConfig(name="test", memory_mb=32768)  # Maximum

    # Invalid memory values should be rejected by Pydantic
    with pytest.raises(ValueError):
        SandboxConfig(name="test", memory_mb=512)  # Too low

    with pytest.raises(ValueError):
        SandboxConfig(name="test", memory_mb=65536)  # Too high


def test_empty_folders_and_commands():
    """Test configuration with no folders or commands."""
    helper = WindowsSandboxHelper()

    config = SandboxConfig(name="minimal-sandbox", memory_mb=2048)

    xml = helper._generate_wsx_config(config)

    # Should have basic config but no MappedFolders or LogonCommand sections
    assert "<Configuration>" in xml
    assert "<VGpu>Enable</VGpu>" in xml
    assert "<MappedFolders>" not in xml
    assert "<LogonCommand>" not in xml


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

