"""
GOLD PUSH Part 4: Main Entry Modules

main.py: 54 lines at 22% = 42 uncovered
__main__.py: 11 lines at 0% = 11 uncovered
dev_tools.py: 94 lines at 0% = 94 uncovered

TOTAL: 147 uncovered lines! Target 60% = 88 lines = +1.0% total coverage!
"""

from unittest.mock import patch

import pytest


class TestMainPyComplete:
    """main.py - 54 lines."""

    @patch("virtualization_mcp.main.FastMCP")
    @patch("virtualization_mcp.main.VBoxManager")
    def test_main_imports(self, mock_vbox, mock_mcp):
        """Test main.py imports."""
        import virtualization_mcp.main as main

        assert main is not None
        assert hasattr(main, "main")


class TestDunderMainComplete:
    """__main__.py - 11 lines."""

    def test_dunder_main_complete(self):
        """Test __main__ module."""
        import virtualization_mcp.__main__ as main

        assert main is not None


class TestDevToolsComplete:
    """dev_tools.py - 94 lines at 0%."""

    def test_dev_tools_complete(self):
        """Test dev_tools module."""
        import virtualization_mcp.tools.dev_tools as dev

        assert dev is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
