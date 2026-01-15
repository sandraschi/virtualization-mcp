"""
Portfolio Manager for virtualization-mcp

Manages preconfigured portfolios (collections of files and commands) that can be
applied to Windows Sandbox or VirtualBox VMs.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages portfolios for sandboxes and VMs."""

    def __init__(self, portfolios_dir: Path | None = None):
        """Initialize the portfolio manager.

        Args:
            portfolios_dir: Path to the portfolios directory
        """
        if portfolios_dir is None:
            # Default to config/portfolios relative to package root
            portfolios_dir = Path(__file__).parent.parent.parent / "config" / "portfolios"

        self.portfolios_dir = portfolios_dir
        self._portfolios_cache: dict[str, dict[str, Any]] = {}

        # Ensure portfolios directory exists
        self.portfolios_dir.mkdir(parents=True, exist_ok=True)

    def load_portfolio(self, portfolio_name: str) -> dict[str, Any]:
        """Load a portfolio by name.

        Args:
            portfolio_name: Name of the portfolio to load

        Returns:
            Portfolio configuration dictionary

        Raises:
            ValueError: If portfolio not found or invalid
        """
        # Check cache first
        if portfolio_name in self._portfolios_cache:
            return self._portfolios_cache[portfolio_name]

        # Look for YAML file
        portfolio_file = self.portfolios_dir / f"{portfolio_name}.yaml"

        if not portfolio_file.exists():
            available = self.list_available_portfolios()
            raise ValueError(
                f"Portfolio '{portfolio_name}' not found. "
                f"Available portfolios: {', '.join(available)}"
            )

        try:
            with open(portfolio_file, encoding="utf-8") as f:
                portfolio = yaml.safe_load(f)

            if not isinstance(portfolio, dict):
                raise ValueError(f"Invalid portfolio file format: {portfolio_file}")

            # Validate required fields
            if "name" not in portfolio:
                portfolio["name"] = portfolio_name

            # Cache it
            self._portfolios_cache[portfolio_name] = portfolio

            logger.info(f"Loaded portfolio: {portfolio_name}")
            return portfolio

        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse portfolio file {portfolio_file}: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load portfolio {portfolio_name}: {e}") from e

    def list_available_portfolios(self) -> list[str]:
        """List all available portfolio names.

        Returns:
            List of portfolio names
        """
        if not self.portfolios_dir.exists():
            return []

        portfolios = []
        for file in self.portfolios_dir.glob("*.yaml"):
            portfolio_name = file.stem
            portfolios.append(portfolio_name)

        return sorted(portfolios)

    def get_portfolio_info(self, portfolio_name: str) -> dict[str, Any]:
        """Get portfolio information without full details.

        Args:
            portfolio_name: Name of the portfolio

        Returns:
            Dictionary with portfolio metadata
        """
        portfolio = self.load_portfolio(portfolio_name)
        return {
            "name": portfolio.get("name", portfolio_name),
            "description": portfolio.get("description", ""),
            "targets": portfolio.get("targets", []),  # ['sandbox', 'vm'] or ['sandbox']
            "version": portfolio.get("version", "1.0.0"),
        }

    def clear_cache(self):
        """Clear the portfolios cache."""
        self._portfolios_cache.clear()

