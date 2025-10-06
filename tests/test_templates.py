"""
Tests for the vboxmcp VM templates functionality.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from virtualization_mcp.services.vm.templates import VMTemplateMixin

class TestVMTemplateMixin:
    """Tests for the VMTemplateMixin class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.templates = VMTemplateMixin(self.vm_service)
        self.template_name = "ubuntu-2004"
        self.template_dir = tmp_path / "templates"
        self.template_dir.mkdir()
        
        # Create a test template file
        self.template_file = self.template_dir / f"{self.template_name}.json"
        self.template_file.write_text('''
        {
            "name": "ubuntu-2004",
            "description": "Ubuntu 20.04 LTS",
            "os_type": "Ubuntu_64",
            "memory_mb": 4096,
            "cpus": 2,
            "storage": [
                {
                    "size_gb": 30,
                    "type": "vdi",
                    "controller": "SATA"
                }
            ],
            "network": [
                {
                    "type": "nat",
                    "adapter": 1
                }
            ]
        }
        ''')
        
        # Patch the template directory
        self.templates.TEMPLATE_DIR = str(self.template_dir)
        
    def test_list_templates(self):
        """Test listing available VM templates."""
        # Call the method
        result = self.templates.list_templates()
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == self.template_name
        
    def test_get_template(self):
        """Test getting a specific VM template."""
        # Call the method
        result = self.templates.get_template(self.template_name)
        
        # Assertions
        assert result["name"] == "ubuntu-2004"
        assert result["memory_mb"] == 4096
        assert result["cpus"] == 2
        
    def test_create_template(self):
        """Test creating a new VM template."""
        # Test data
        template_data = {
            "name": "ubuntu-2204",
            "description": "Ubuntu 22.04 LTS",
            "os_type": "Ubuntu_64",
            "memory_mb": 4096,
            "cpus": 2
        }
        
        # Call the method
        result = self.templates.create_template("ubuntu-2204", template_data)
        
        # Assertions
        assert result["status"] == "success"
        assert (self.template_dir / "ubuntu-2204.json").exists()
        
    def test_delete_template(self):
        """Test deleting a VM template."""
        # Call the method
        result = self.templates.delete_template(self.template_name)
        
        # Assertions
        assert result["status"] == "success"
        assert not self.template_file.exists()
        
    @pytest.mark.asyncio
    async def test_deploy_from_template(self, mock_vbox):
        """Test deploying a VM from a template."""
        # Setup mock
        mock_vbox.create_vm.return_value = {"status": "success"}
        
        # Call the method
        result = await self.templates.deploy_from_template(
            "new-vm",
            self.template_name,
            {"memory_mb": 8192}  # Override memory
        )
        
        # Assertions
        assert result["status"] == "success"
        self.vm_service.vbox_manager.create_vm.assert_called_once()
        
    def test_validate_template(self):
        """Test template validation."""
        # Valid template
        valid_template = {
            "name": "test-template",
            "os_type": "Ubuntu_64",
            "memory_mb": 4096,
            "cpus": 2,
            "storage": [{"size_gb": 30, "type": "vdi"}],
            "network": [{"type": "nat"}]
        }
        
        # Should not raise an exception
        self.templates._validate_template(valid_template)
        
        # Invalid template (missing required fields)
        invalid_template = {"name": "invalid"}
        with pytest.raises(ValueError):
            self.templates._validate_template(invalid_template)
