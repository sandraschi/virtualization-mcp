"""
Templates - VM template management system
Handles template-based VM creation and configuration management
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    VM Template management system
    
    Provides Austrian dev efficiency with template-based rapid VM deployment
    and standardized configurations for different use cases.
    """
    
    def __init__(self, templates_path: Optional[Path] = None):
        """
        Initialize template manager
        
        Args:
            templates_path: Path to templates YAML file
        """
        self.templates_path = templates_path or Path("config/vm_templates.yaml")
        self._templates = None
    
    @property
    def templates(self) -> Dict[str, Any]:
        """Load and cache templates"""
        if self._templates is None:
            self._templates = self.load_templates()
        return self._templates
    
    def load_templates(self) -> Dict[str, Any]:
        """Load templates from YAML file with fallback to defaults"""
        try:
            if self.templates_path.exists():
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    templates = data.get('templates', {})
                    
                    # Validate templates
                    validated_templates = {}
                    for name, config in templates.items():
                        if self._validate_template(name, config):
                            validated_templates[name] = config
                        else:
                            logger.warning(f"Invalid template '{name}' - skipping")
                    
                    logger.info(f"Loaded {len(validated_templates)} templates from {self.templates_path}")
                    return validated_templates
            else:
                logger.info(f"Templates file not found: {self.templates_path} - using defaults")
                return self._get_default_templates()
                
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return self._get_default_templates()
    
    def _validate_template(self, name: str, config: Dict[str, Any]) -> bool:
        """Validate template configuration"""
        required_fields = ["os_type", "memory_mb", "disk_gb"]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Template '{name}' missing required field: {field}")
                return False
        
        # Validate memory
        if not isinstance(config["memory_mb"], int) or config["memory_mb"] < 128:
            logger.error(f"Template '{name}' has invalid memory: {config['memory_mb']}")
            return False
        
        # Validate disk
        if not isinstance(config["disk_gb"], int) or config["disk_gb"] < 1:
            logger.error(f"Template '{name}' has invalid disk size: {config['disk_gb']}")
            return False
        
        return True
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Return comprehensive default templates"""
        return {
            "ubuntu-dev": {
                "os_type": "Ubuntu_64",
                "memory_mb": 4096,
                "disk_gb": 25,
                "network": "NAT",
                "description": "Ubuntu development environment with Docker",
                "post_install": [
                    "docker",
                    "git",
                    "nodejs",
                    "python3"
                ],
                "recommended_snapshots": [
                    "fresh-install",
                    "dev-tools-ready"
                ]
            },
            "windows-test": {
                "os_type": "Windows11_64",
                "memory_mb": 8192,
                "disk_gb": 60,
                "network": "NAT",
                "description": "Windows testing environment",
                "post_install": [
                    "chocolatey",
                    "visual-studio-code",
                    "git"
                ],
                "recommended_snapshots": [
                    "clean-windows",
                    "dev-ready"
                ]
            },
            "minimal-linux": {
                "os_type": "Ubuntu_64",
                "memory_mb": 1024,
                "disk_gb": 10,
                "network": "NAT",
                "description": "Minimal Linux for quick tests",
                "use_cases": [
                    "CLI testing",
                    "Service validation",
                    "Quick experiments"
                ]
            },
            "database-server": {
                "os_type": "Ubuntu_64",
                "memory_mb": 6144,
                "disk_gb": 40,
                "network": "NAT",
                "description": "Database server with PostgreSQL/MySQL",
                "post_install": [
                    "postgresql",
                    "mysql-server",
                    "redis-server"
                ],
                "port_forwards": [
                    {"guest": 5432, "host": 5432, "service": "PostgreSQL"},
                    {"guest": 3306, "host": 3306, "service": "MySQL"},
                    {"guest": 6379, "host": 6379, "service": "Redis"}
                ]
            },
            "web-server": {
                "os_type": "Ubuntu_64",
                "memory_mb": 2048,
                "disk_gb": 20,
                "network": "NAT",
                "description": "Web server with Nginx and PHP",
                "post_install": [
                    "nginx",
                    "php8.1",
                    "php8.1-fpm",
                    "certbot"
                ],
                "port_forwards": [
                    {"guest": 80, "host": 8080, "service": "HTTP"},
                    {"guest": 443, "host": 8443, "service": "HTTPS"}
                ]
            },
            "docker-host": {
                "os_type": "Ubuntu_64",
                "memory_mb": 4096,
                "disk_gb": 30,
                "network": "NAT",
                "description": "Docker host for container testing",
                "post_install": [
                    "docker",
                    "docker-compose",
                    "portainer"
                ],
                "port_forwards": [
                    {"guest": 2376, "host": 2376, "service": "Docker API"},
                    {"guest": 9000, "host": 9000, "service": "Portainer"}
                ]
            },
            "security-test": {
                "os_type": "Ubuntu_64",
                "memory_mb": 2048,
                "disk_gb": 15,
                "network": "NAT",
                "description": "Security testing environment",
                "post_install": [
                    "nmap",
                    "wireshark",
                    "metasploit-framework"
                ],
                "use_cases": [
                    "Penetration testing",
                    "Vulnerability assessment",
                    "Network analysis"
                ]
            }
        }
    
    def get_template(self, name: str) -> Dict[str, Any]:
        """Get specific template by name"""
        if name not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(f"Template '{name}' not found. Available: {available}")
        
        return self.templates[name].copy()
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates with metadata"""
        templates_list = []
        
        for name, config in self.templates.items():
            template_info = {
                "name": name,
                "description": config.get("description", "No description"),
                "os_type": config.get("os_type", "Unknown"),
                "memory_mb": config.get("memory_mb", 0),
                "disk_gb": config.get("disk_gb", 0),
                "network": config.get("network", "NAT"),
                "use_cases": config.get("use_cases", []),
                "post_install": config.get("post_install", []),
                "port_forwards": config.get("port_forwards", []),
                "recommended_snapshots": config.get("recommended_snapshots", [])
            }
            templates_list.append(template_info)
        
        return sorted(templates_list, key=lambda x: x["name"])
    
    def create_template(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new template"""
        if name in self.templates:
            raise ValueError(f"Template '{name}' already exists")
        
        if not self._validate_template(name, config):
            raise ValueError(f"Invalid template configuration for '{name}'")
        
        # Add template to memory
        self.templates[name] = config.copy()
        
        # Save to file
        self.save_templates()
        
        return {
            "success": True,
            "template_name": name,
            "message": f"Template '{name}' created successfully"
        }
    
    def update_template(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        
        if not self._validate_template(name, config):
            raise ValueError(f"Invalid template configuration for '{name}'")
        
        # Update template
        self.templates[name] = config.copy()
        
        # Save to file
        self.save_templates()
        
        return {
            "success": True,
            "template_name": name,
            "message": f"Template '{name}' updated successfully"
        }
    
    def delete_template(self, name: str) -> Dict[str, Any]:
        """Delete template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        
        # Remove from memory
        del self.templates[name]
        
        # Save to file
        self.save_templates()
        
        return {
            "success": True,
            "template_name": name,
            "message": f"Template '{name}' deleted successfully"
        }
    
    def save_templates(self) -> None:
        """Save templates to YAML file"""
        try:
            # Ensure config directory exists
            self.templates_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data structure
            data = {
                "templates": self.templates,
                "metadata": {
                    "version": "1.0",
                    "description": "VirtualBox MCP Server VM Templates",
                    "created_by": "VirtualBox MCP",
                    "last_updated": __import__('datetime').datetime.now().isoformat()
                }
            }
            
            # Write to file
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True, indent=2)
            
            logger.info(f"Templates saved to {self.templates_path}")
            
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
            raise
    
    def reload_templates(self) -> Dict[str, Any]:
        """Reload templates from file"""
        self._templates = None
        templates = self.templates  # This will trigger reload
        
        return {
            "success": True,
            "templates_count": len(templates),
            "message": f"Reloaded {len(templates)} templates"
        }
    
    def get_template_for_use_case(self, use_case: str) -> List[Dict[str, Any]]:
        """Find templates suitable for specific use case"""
        matching_templates = []
        
        use_case_lower = use_case.lower()
        
        for name, config in self.templates.items():
            # Check use_cases field
            template_use_cases = [uc.lower() for uc in config.get("use_cases", [])]
            
            # Check description
            description = config.get("description", "").lower()
            
            # Check post_install packages
            packages = [pkg.lower() for pkg in config.get("post_install", [])]
            
            if (use_case_lower in template_use_cases or 
                use_case_lower in description or
                any(use_case_lower in pkg for pkg in packages)):
                
                matching_templates.append({
                    "name": name,
                    "config": config,
                    "relevance_score": self._calculate_relevance(use_case_lower, config)
                })
        
        # Sort by relevance score
        matching_templates.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return matching_templates
    
    def _calculate_relevance(self, use_case: str, config: Dict[str, Any]) -> float:
        """Calculate relevance score for template and use case"""
        score = 0.0
        
        # Exact match in use_cases
        use_cases = [uc.lower() for uc in config.get("use_cases", [])]
        if use_case in use_cases:
            score += 10.0
        
        # Partial match in use_cases
        for uc in use_cases:
            if use_case in uc or uc in use_case:
                score += 5.0
        
        # Match in description
        description = config.get("description", "").lower()
        if use_case in description:
            score += 3.0
        
        # Match in packages
        packages = [pkg.lower() for pkg in config.get("post_install", [])]
        for pkg in packages:
            if use_case in pkg or pkg in use_case:
                score += 2.0
        
        return score



