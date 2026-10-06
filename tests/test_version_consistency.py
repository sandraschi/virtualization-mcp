"""Server-reported version must track the package version (Glama/clients read it)."""

import virtualization_mcp
from virtualization_mcp.config import settings


def test_app_version_matches_package_version():
    assert settings.APP_VERSION == virtualization_mcp.__version__
