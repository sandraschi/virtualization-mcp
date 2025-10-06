# Contributing to VirtualBox MCP Server

## 🎯 Austrian Development Philosophy

This project follows **Austrian efficiency principles**:

- **Direct, purposeful code** - No unnecessary complexity
- **Immediate actionable solutions** - Clear error messages and next steps  
- **Comprehensive validation** - Every failure path handled
- **Production-ready quality** - Working solutions in hours, not days

## 🚀 Quick Start for Contributors

### 1. Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd vboxmcp
pip install -r requirements.txt
cp .env.example .env

# Install development dependencies
pip install pytest black pre-commit

# Setup pre-commit hooks
pre-commit install
```

### 2. Test Your Changes

```bash
# Run MCP Inspector for manual testing
fastmcp dev server.py
# Opens http://127.0.0.1:6274

# Run automated tests
python -m pytest tests/

# Format code
black .
```

### 3. Contribution Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit frequently
git add .
git commit -m "feat: descriptive commit message"

# Push and create pull request
git push -u origin feature/your-feature-name
```

## 📋 Development Standards

### Code Quality

- **Error handling**: Every VBoxManage operation must be wrapped in try/catch
- **Validation**: All user inputs sanitized and validated
- **Documentation**: Every MCP tool fully documented with examples
- **Austrian directness**: Clear, actionable error messages

### Commit Message Format

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature or MCP tool
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
git commit -m "feat: add VM cloning tool with linked clone support"
git commit -m "fix: handle VBoxManage timeout errors gracefully"
git commit -m "docs: update API reference with new snapshot tools"
```

### Code Style

- **Black formatting**: All Python code formatted with Black
- **Type hints**: Use type hints for function parameters and returns
- **Docstrings**: Every function documented with args, returns, and examples
- **Austrian naming**: Clear, descriptive variable and function names

### MCP Tool Standards

```python
@mcp.tool()
def tool_name(param: str, optional_param: bool = True) -> Dict[str, Any]:
    """Tool description with clear use case.
    
    Args:
        param: Description of required parameter
        optional_param: Description of optional parameter
        
    Returns:
        Dict with success/failure and descriptive message
        
    Example:
        tool_name("example-vm", optional_param=False)
    """
    try:
        # Validate inputs
        if not param:
            return {"success": False, "error": "Parameter cannot be empty"}
            
        # Execute operation
        result = manager.execute_operation(param)
        
        # Return Austrian-direct response
        return {
            "success": True,
            "message": f"✅ Operation completed successfully",
            "data": result,
            "next_steps": "Suggested next actions"
        }
        
    except VBoxManagerError as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Operation failed: {e}",
            "troubleshooting": "Direct solution steps"
        }
```

## 🧪 Testing Guidelines

### Manual Testing

1. **MCP Inspector testing**: Every new tool tested in browser
2. **Real VM operations**: Create, start, snapshot, destroy workflow
3. **Error scenarios**: Test with invalid inputs, missing VMs, etc.
4. **Template validation**: All VM templates tested

### Automated Testing

```python
def test_vm_operation():
    """Test follows Austrian testing: direct, comprehensive, actionable."""
    # Setup - clear test state
    cleanup_test_vms()
    
    # Execute - single operation focus
    result = create_vm("test-vm", "minimal-linux")
    
    # Validate - comprehensive checks
    assert result["success"] is True
    assert "test-vm" in list_vms()["data"]
    
    # Cleanup - leave clean state
    cleanup_test_vms()
```

### Test Categories

- **Unit tests**: Individual component testing
- **Integration tests**: Full workflow testing
- **Error handling tests**: Failure path validation
- **Template tests**: All VM templates validated

## 📚 Documentation Standards

### API Documentation

- **Every MCP tool documented** with purpose, parameters, returns
- **Real examples** showing common usage patterns
- **Error scenarios** with troubleshooting steps
- **Austrian directness** - no fluff, immediate utility

### Code Documentation

```python
class VBoxManager:
    """VirtualBox CLI wrapper with comprehensive error handling.
    
    Provides robust interface to VBoxManage with Austrian efficiency:
    - Direct error identification
    - Immediate actionable solutions  
    - Comprehensive validation
    - Production-ready reliability
    """
    
    def execute_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute VBoxManage command with full error handling.
        
        Args:
            args: VBoxManage command arguments
            
        Returns:
            Dict with success status, data, and error details
            
        Raises:
            VBoxManagerError: When VBoxManage operation fails
            
        Example:
            result = manager.execute_command(["showvminfo", "vm-name"])
        """
```

## 🔧 Adding New Features

### MCP Tools

1. **Define purpose**: What specific VM operation does this enable?
2. **Plan parameters**: Required/optional inputs with validation
3. **Implementation**: Follow error handling patterns
4. **Documentation**: Complete API reference entry
5. **Testing**: Manual + automated validation

### VM Templates

```yaml
# config/vm_templates.yaml
new-template:
  os_type: "Ubuntu_64"
  memory_mb: 4096
  disk_gb: 25
  network: "NAT"
  description: "Clear use case description"
  use_cases:
    - "Specific development scenario"
    - "Testing environment type"
  post_install:
    - required-package-1
    - required-package-2
```

### Configuration Options

- **Environment variables**: Add to .env.example with documentation
- **Settings YAML**: Add to config/settings.yaml with defaults
- **Validation**: Ensure all options validated on startup

## 🚨 Error Handling Standards

### Austrian Error Philosophy

```python
# ❌ Vague, unhelpful
return {"success": False, "error": "Something went wrong"}

# ✅ Austrian directness
return {
    "success": False,
    "error": "VM 'test-vm' not found",
    "message": "❌ Cannot start VM: 'test-vm' does not exist",
    "troubleshooting": "Use list_vms() to see available VMs or create_vm() to create it",
    "next_steps": ["Check VM name spelling", "Create VM if missing", "Use list_vms() to verify"]
}
```

### Error Categories

- **User input errors**: Clear parameter validation messages
- **VirtualBox errors**: Translate VBoxManage errors to actionable solutions
- **System errors**: Direct identification of resource/permission issues
- **Network errors**: Specific troubleshooting for connectivity problems

## 🎯 Review Criteria

### Pull Request Requirements

- [ ] **Functionality**: Feature works as documented
- [ ] **Error handling**: All failure paths handled with Austrian directness
- [ ] **Documentation**: API reference updated, examples provided
- [ ] **Testing**: Manual MCP Inspector + automated tests pass
- [ ] **Code quality**: Black formatted, type hints, comprehensive docstrings
- [ ] **Austrian efficiency**: No unnecessary complexity, immediate utility

### Code Review Focus

1. **Error handling completeness**: Every VBoxManage call protected
2. **Austrian messaging**: Error messages direct and actionable
3. **Documentation accuracy**: Examples work as shown
4. **Test coverage**: Both success and failure paths tested
5. **Performance efficiency**: Operations complete in reasonable time

## 🏆 Recognition

### Contributor Levels

- **Code contributors**: New tools, bug fixes, improvements
- **Documentation contributors**: API docs, examples, guides
- **Testing contributors**: Test cases, validation scenarios
- **Template contributors**: New VM templates, use cases

### Austrian Achievement Standards

- **Efficiency**: Working solutions delivered rapidly
- **Directness**: Clear, actionable code and documentation
- **Reliability**: Comprehensive error handling and validation
- **Utility**: Immediate practical value for VirtualBox automation

## 📞 Getting Help

### Questions and Discussion

- **GitHub Issues**: Bug reports and feature requests
- **Pull Request reviews**: Implementation feedback
- **Documentation clarifications**: API or setup questions

### Austrian Support Philosophy

- **Direct answers**: No runaround, immediate solutions
- **Actionable guidance**: Specific steps to resolve issues
- **Comprehensive help**: Cover the complete solution path
- **Efficient resolution**: Fast turnaround on questions

---

**Contributing with Austrian efficiency: Direct, purposeful, immediately useful.** 🚀

*Every contribution makes VirtualBox automation through Claude Desktop more powerful and reliable.*
