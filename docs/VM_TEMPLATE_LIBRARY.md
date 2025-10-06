# VM Template Library Design

## 1. Overview
This document outlines the design for a template library system that allows users to easily create, share, and deploy pre-configured virtual machines.

## 2. Template Structure

### 2.1 Template Definition
```yaml
# template-definition.yaml
name: "python-dev"
version: "1.0.0"
description: "Python 3.10 development environment"
author: "vboxmcp Team"

# Base image or requirements
base_image: "ubuntu:22.04"
min_ram: 2048  # MB
min_disk: 20000  # MB
min_cores: 2

# Software packages to install
packages:
  system:
    - git
    - curl
  python:
    - python3.10
    - python3-pip
    - python3-venv

# Post-installation scripts
scripts:
  - name: Install Python packages
    command: pip install -r requirements.txt
    working_dir: /tmp
    run_as: root

# Environment variables
environment:
  PYTHONUNBUFFERED: "1"
  
# Ports to expose
ports:
  - 8000  # Default web server port
  - 8080  # Alternative port

# Shared folders
shared_folders:
  - name: code
    host_path: ~/projects
    guest_path: /home/developer/code
    read_only: false

# Metadata
metadata:
  tags: ["python", "development", "ubuntu"]
  license: "MIT"
  source: "https://github.com/example/python-dev-template"
```

## 3. Repository Structure

### 3.1 Local Repository
```
~/.vboxmcp/templates/
├── python-dev/
│   ├── template-definition.yaml
│   ├── requirements.txt
│   ├── setup.sh
│   └── README.md
└── nodejs-dev/
    └── ...
```

### 3.2 Remote Repository
- Host templates in a Git repository
- Support for multiple template sources
- Version control for templates
- Signed templates for verification

## 4. Template Lifecycle

### 4.1 Creation
1. Define template metadata and requirements
2. Create provisioning scripts
3. Test template in isolation
4. Package and sign template

### 4.2 Distribution
- Publish to template registry
- Share via URL or file
- Support for private repositories

### 4.3 Usage
```python
# Example: Create VM from template
vm = vm_manager.create_from_template(
    name="my-python-dev",
    template="python-dev",
    version="1.0.0",
    parameters={
        "memory": 4096,
        "cpus": 4,
        "disk_size": 50000
    }
)
```

## 5. Security Considerations
- Template validation
- Digital signatures
- Sandboxed execution
- Resource limits
- Audit logging

## 6. Future Enhancements
- Template composition
- Automated testing
- Dependency resolution
- Template marketplace
