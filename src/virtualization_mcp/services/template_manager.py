"""
Template Manager for virtualization-mcp

Manages VM templates for easy deployment of preconfigured virtual machines.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages VM templates and template-based deployments."""

    def __init__(self, templates_path: Path | None = None):
        """Initialize the template manager.

        Args:
            templates_path: Path to the templates configuration file
        """
        self.templates_path = (
            templates_path or Path(__file__).parent.parent / "config" / "vm_templates.yaml"
        )
        self._templates_cache: list[dict[str, Any]] | None = None

    def load_templates(self) -> list[dict[str, Any]]:
        """Load templates from the configuration file.

        Returns:
            List of template configurations
        """
        if not self.templates_path.exists():
            logger.warning(f"Templates file not found at {self.templates_path}")
            return []

        try:
            with open(self.templates_path, encoding="utf-8") as f:
                templates = yaml.safe_load(f)
                return templates if isinstance(templates, list) else []
        except Exception as e:
            logger.error(f"Failed to load templates from {self.templates_path}: {e}")
            return []

    def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates.

        Returns:
            List of template configurations
        """
        if self._templates_cache is None:
            self._templates_cache = self.load_templates()
        return self._templates_cache.copy()

    def get_template(self, template_name: str) -> dict[str, Any] | None:
        """Get a specific template by name.

        Args:
            template_name: Name of the template to retrieve

        Returns:
            Template configuration or None if not found
        """
        templates = self.list_templates()
        for template in templates:
            if template.get("name") == template_name:
                return template.copy()
        return None

    def validate_template(self, template: dict[str, Any]) -> bool:
        """Validate a template configuration.

        Args:
            template: Template configuration to validate

        Returns:
            True if template is valid, False otherwise
        """
        required_fields = ["name", "os_type"]
        for field in required_fields:
            if field not in template:
                logger.error(f"Template missing required field: {field}")
                return False

        # Validate numeric fields
        numeric_fields = ["memory", "cpus", "disk_size"]
        for field in numeric_fields:
            if field in template and not isinstance(template[field], (int, float)):
                logger.error(f"Template field '{field}' must be numeric")
                return False

        return True

    def create_template(self, template: dict[str, Any]) -> bool:
        """Create a new template.

        Args:
            template: Template configuration to create

        Returns:
            True if template was created successfully, False otherwise
        """
        if not self.validate_template(template):
            return False

        templates = self.list_templates()

        # Check if template with same name already exists
        for existing in templates:
            if existing.get("name") == template.get("name"):
                logger.error(f"Template with name '{template['name']}' already exists")
                return False

        # Add the new template
        templates.append(template)

        try:
            with open(self.templates_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(templates, f, default_flow_style=False, indent=2)

            # Clear cache to force reload
            self._templates_cache = None
            logger.info(f"Created template: {template['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False

    def delete_template(self, template_name: str) -> bool:
        """Delete a template.

        Args:
            template_name: Name of the template to delete

        Returns:
            True if template was deleted successfully, False otherwise
        """
        templates = self.list_templates()

        # Find and remove the template
        for i, template in enumerate(templates):
            if template.get("name") == template_name:
                templates.pop(i)

                try:
                    with open(self.templates_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(templates, f, default_flow_style=False, indent=2)

                    # Clear cache to force reload
                    self._templates_cache = None
                    logger.info(f"Deleted template: {template_name}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to save templates after deletion: {e}")
                    return False

        logger.error(f"Template '{template_name}' not found")
        return False


__all__ = ["TemplateManager"]
