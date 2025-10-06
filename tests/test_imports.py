"""
Basic import tests to verify the package can be imported correctly.
"""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        import virtualization_mcp
        assert virtualization-mcp is not None
    except ImportError as e:
        pytest.fail(f"Failed to import virtualization_mcp: {e}")


def test_config_import():
    """Test that config module can be imported."""
    try:
        from virtualization_mcp.config import settings
        assert settings is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")


def test_tools_import():
    """Test that tools module can be imported."""
    try:
        from virtualization_mcp.tools import register_all_tools
        assert register_all_tools is not None
    except ImportError as e:
        pytest.fail(f"Failed to import tools: {e}")


def test_server_import():
    """Test that server module can be imported."""
    try:
        from virtualization_mcp.all_tools_server import main
        assert main is not None
    except ImportError as e:
        pytest.fail(f"Failed to import server: {e}")


def test_pytest_working():
    """Simple test to verify pytest is working."""
    assert True


if __name__ == "__main__":
    pytest.main([__file__])



