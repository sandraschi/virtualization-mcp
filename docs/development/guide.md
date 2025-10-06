# virtualization-mcp Development Guide

## Table of Contents
1. [Code Structure](#code-structure)
2. [Development Setup](#development-setup)
3. [Adding New Features](#adding-new-features)
4. [Testing](#testing)
5. [Debugging](#debugging)
6. [Code Style](#code-style)
7. [Documentation](#documentation)
8. [Contributing](#contributing)

## Code Structure

```
virtualization-mcp/
├── src/
│   └── virtualization-mcp/
│       ├── __init__.py         # Package initialization
│       ├── server.py           # Main FastAPI application
│       ├── config.py           # Configuration management
│       ├── models.py           # Data models
│       └── vbox/              # VirtualBox integration
│           ├── __init__.py
│           ├── manager.py      # Main VirtualBox manager
│           ├── vm_operations.py # VM operations
│           ├── snapshots.py    # Snapshot management
│           └── networking.py   # Network configuration
├── tests/                     # Test suite
├── dxt/                       # DXT packaging files
└── docs/                      # Documentation
```

## Development Setup

### Prerequisites

- Python 3.8+
- VirtualBox 6.1+
- VirtualBox SDK
- Poetry (for dependency management)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/virtualization-mcp.git
   cd virtualization-mcp
   ```

2. Set up a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]
   ```

3. Configure VirtualBox SDK:
   - Download the VirtualBox SDK
   - Install it according to the platform-specific instructions
   - Set the `VBOX_INSTALL_PATH` environment variable

## Adding New Features

### 1. Create a new branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Implement your feature

Follow the project's code style and architecture patterns. Add tests for your code.

### 3. Add API endpoints (if applicable)

Add new endpoints to `server.py` following the existing patterns:

```python
@router.post("/vms/{vm_name}/custom-action")
async def custom_action(
    vm_name: str,
    action: str = Body(..., description="Action to perform"),
    params: Dict = Body(default_factory=dict)
):
    """
    Custom action for a VM.
    
    Args:
        vm_name: Name of the VM
        action: Action to perform
        params: Action parameters
        
    Returns:
        Result of the action
    """
    try:
        result = await vbox_manager.custom_action(vm_name, action, **params)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error in custom_action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Update documentation

Update the relevant documentation in the `docs` directory.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_vm_operations.py

# Run tests with coverage report
pytest --cov=virtualization-mcp tests/
```

### Writing Tests

Follow these patterns when writing tests:

```python
import pytest
from virtualization-mcp.vbox.manager import VBoxManager

class TestVMManagement:
    @pytest.fixture
    def vm_manager(self):
        return VBoxManager()
    
    def test_create_vm(self, vm_manager):
        """Test VM creation with valid parameters."""
        vm_name = "test-vm-1"
        try:
            result = vm_manager.create_vm(
                name=vm_name,
                template="ubuntu-20.04",
                memory_mb=2048,
                disk_gb=20
            )
            assert result["status"] == "success"
            assert vm_manager.vm_exists(vm_name)
        finally:
            if vm_manager.vm_exists(vm_name):
                vm_manager.delete_vm(vm_name, force=True)
```

## Debugging

### Enabling Debug Mode

Start the server in debug mode:

```bash
python -m virtualization-mcp.server --debug
```

### Using the Debugger

Set breakpoints in your code:

```python
import pdb; pdb.set_trace()  # Python debugger
```

Or use VS Code's debugger by creating a `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: virtualization-mcp",
            "type": "python",
            "request": "launch",
            "module": "virtualization-mcp.server",
            "args": ["--debug"],
            "justMyCode": false
        }
    ]
}
```

## Code Style

Follow these style guidelines:

- **PEP 8** for Python code
- **Google style** for docstrings
- Type hints for all function parameters and return values
- Maximum line length: 100 characters

Run the linter and formatter:

```bash
# Auto-format code
black .

# Sort imports
isort .

# Check for style issues
pylint virtualization-mcp/

# Check types
mypy virtualization-mcp/
```

## Documentation

### Writing Documentation

- Use Markdown for all documentation
- Include code examples for all public APIs
- Document all parameters, return values, and exceptions
- Keep documentation up to date with code changes

### Building Documentation

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build the documentation
cd docs
make html
```

The generated documentation will be available in `docs/_build/html`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

### Pull Request Checklist

- [ ] Code follows the style guidelines
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] Changes are well-documented
- [ ] No sensitive data is included in commits

### Code Review Process

1. Automated checks (tests, linting, type checking)
2. Manual code review by maintainers
3. Address any feedback
4. Merge after approval



