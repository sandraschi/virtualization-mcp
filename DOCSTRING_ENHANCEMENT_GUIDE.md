# Comprehensive Docstring Enhancement Guide

## Status: IN PROGRESS

This guide documents the systematic improvement of all tool docstrings across the virtualization-mcp project to production quality standards.

## Progress Tracker

### ✅ Completed (7/50+ tools)

**Windows Sandbox Module:**
- ✅ MappedFolder class
- ✅ SandboxConfig class
- ✅ WindowsSandboxHelper class
- ✅ create_windows_sandbox()
- ✅ list_running_sandboxes()
- ✅ stop_sandbox()
- ✅ _generate_wsx_config()

**VM Tools (6/11):**
- ✅ list_vms()
- ✅ get_vm_info()
- ✅ create_vm()
- ✅ start_vm()
- ✅ stop_vm()
- ✅ delete_vm()

### 🔄 In Progress (5/11 VM tools remaining)

- ⏳ clone_vm()
- ⏳ modify_vm()
- ⏳ pause_vm()
- ⏳ resume_vm()
- ⏳ reset_vm()

### 📋 Pending (~40+ tools)

**Snapshot Tools:**
- create_snapshot()
- restore_snapshot()
- delete_snapshot()
- list_snapshots()

**Storage Tools:**
- create_storage_controller()
- attach_storage()
- detach_storage()
- list_storage_controllers()

**Network Tools:**
- create_hostonly_network()
- configure_network_adapter()
- list_hostonly_networks()
- remove_hostonly_network()

**System Tools:**
- get_system_info()
- get_vbox_version()
- list_ostypes()

**Monitoring Tools:**
- get_vm_metrics()
- monitor_performance()
- get_resource_usage()

**Backup Tools:**
- create_backup()
- restore_backup()
- list_backups()

**Template Tools:**
- create_from_template()
- export_as_template()
- list_templates()

**Port manteau Tools (5 files):**
- vm_management()
- network_management()
- snapshot_management()
- storage_management()
- system_management()

## Docstring Standard

Each tool function docstring should include:

### 1. Summary (1 line)
```python
"""Create a new virtual machine."""
```

### 2. Description (2-3 lines)
What the function does and why you'd use it.

### 3. Args Section
```python
Args:
    param_name: Description (default: value, range: X-Y)
               Additional details about the parameter
               Options: list valid values
```

### 4. Returns Section
```python
Returns:
    Dictionary containing:
        - field1: Description
        - field2: Description
        - ...
```

### 5. Examples Section (3-5 examples)
```python
Examples:
    Basic usage:
        >>> result = await function()

    Advanced usage:
        >>> result = await function(param=value)

    Real-world scenario:
        >>> # Do something practical
```

### 6. Notes Section
```python
Notes:
    - Important behavior details
    - Performance considerations
    - State requirements
    - Best practices
```

### 7. Common Errors (optional but recommended)
```python
Common Errors:
    - "Error message": What it means
    - "Another error": How to fix
```

### 8. Raises Section
```python
Raises:
    No exceptions raised - errors returned in result dictionary
    OR
    ExceptionType: When this happens
```

### 9. See Also Section
```python
See Also:
    - related_function(): Description
    - another_function(): Description
```

## Example: Complete Enhanced Docstring

```python
async def create_vm(
    name: str,
    ostype: str = "Ubuntu_64",
    memory_mb: int = 2048
) -> dict[str, Any]:
    '''Create a new VirtualBox virtual machine.

    Creates a fully configured virtual machine with storage, network, and hardware
    settings. The VM is created with a SATA storage controller and a dynamically
    allocated VDI disk.

    Args:
        name: Unique name for the VM (required, must not already exist)
        ostype: Operating system type identifier (default: "Ubuntu_64")
               Common: Ubuntu_64, Windows10_64, Windows11_64, Debian_64
               Use list_ostypes() to see all 200+ supported types
        memory_mb: RAM allocation in MB (default: 2048, min: 128)
                  Recommended: 2048 for Linux, 4096+ for Windows

    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - vm_name: Name of the created VM
            - uuid: VM UUID if successful
            - message: Status or error message

    Examples:
        Create basic Ubuntu VM:
            >>> result = await create_vm(name="ubuntu-server")
            >>> print(f"Created: {result['vm_name']}")

        Create Windows VM with custom settings:
            >>> result = await create_vm(
            ...     name="windows-dev",
            ...     ostype="Windows11_64",
            ...     memory_mb=8192
            ... )

    Notes:
        - VM is created but not started by default
        - Disk is dynamically allocated VDI format
        - SATA controller created automatically
        - Operation may take 30-60 seconds

    Common Errors:
        - "VM already exists": Choose a different name
        - "Invalid OS type": Use list_ostypes() for valid values

    Raises:
        No exceptions raised - errors returned in result dictionary

    See Also:
        - list_ostypes(): Get supported OS types
        - start_vm(): Start the created VM
        - delete_vm(): Remove the VM
    '''
```

## Tools by Priority

### High Priority (User-Facing MCP Tools)
1. ✅ VM Tools (6/11 done)
2. Snapshot Tools (0/4)
3. Storage Tools (0/4)
4. Network Tools (0/4)
5. System Tools (0/3)

### Medium Priority (Supporting Functions)
6. Monitoring Tools
7. Backup Tools  
8. Template Tools

### Low Priority (Internal/Advanced)
9. Security Tools
10. Dev Tools
11. Example Tools

## Application Strategy

### Phase 1: Core VM Operations ✅ (50% done)
- list_vms, get_vm_info, create_vm, start_vm, stop_vm, delete_vm

### Phase 2: Advanced VM Operations (Next)
- clone_vm, modify_vm, pause_vm, resume_vm, reset_vm

### Phase 3: Snapshot Management
- create_snapshot, restore_snapshot, delete_snapshot, list_snapshots

### Phase 4: Storage Management
- All storage controller and disk operations

### Phase 5: Network Management
- Network adapter and host-only network operations

### Phase 6: System & Monitoring
- System info, metrics, resource monitoring

### Phase 7: Backup & Templates
- Backup/restore and template operations

### Phase 8: Portmanteau Tools
- High-level management interfaces

## Metrics

- **Total Functions**: ~50+
- **Enhanced So Far**: 13 (26%)
- **Target**: 100%
- **Quality Standard**: Windows Sandbox level
  - 3-5 examples per function
  - Comprehensive notes
  - Error documentation
  - Cross-references

## Next Actions

1. ✅ Complete VM tools (5 more functions)
2. Enhance snapshot tools (4 functions)
3. Enhance storage tools (4 functions)
4. Enhance network tools (4 functions)
5. Enhance system tools (3 functions)
6. Continue with remaining modules

## Benefits of Enhanced Docstrings

### For Developers:
- Copy-paste examples
- Clear API documentation
- Error handling guidance
- Type information

### For Claude/AI:
- Better tool understanding
- More accurate suggestions
- Context-aware responses
- Error prevention

### For Users:
- Self-documenting code
- Quick troubleshooting
- Professional documentation
- Easy onboarding

## Testing Strategy

After each module enhancement:
1. Run ruff linting
2. Run pytest for that module
3. Verify no regressions
4. Update progress tracker

## Files to Enhance

### src/virtualization_mcp/tools/
- [x] sandbox/manager.py (7/7 done)
- [~] vm/vm_tools.py (6/11 done)
- [ ] snapshot/snapshot_tools.py
- [ ] storage/storage_tools.py
- [ ] network/network_tools.py
- [ ] system/system_tools.py
- [ ] monitoring/monitoring_tools.py
- [ ] monitoring/metrics_tools.py
- [ ] backup/backup_tools.py
- [ ] security/*.py (4 files)
- [ ] dev/*.py (3 files)
- [ ] portmanteau/*.py (5 files)

Total: ~20 files, ~50+ functions

## Commands for Validation

```bash
# Lint check
uv run ruff check src/virtualization_mcp/tools/

# Run tests
uv run pytest tests/ -v --no-cov

# Check specific module
uv run pytest tests/test_vm_*.py -v
```

## Template Checklist

For each function, ensure:
- [x] Summary line (concise, actionable)
- [x] Description (2-3 sentences)
- [x] Args with defaults, ranges, and options
- [x] Returns with structure breakdown
- [x] 3-5 practical examples
- [x] Notes section with important details
- [x] Common errors (if applicable)
- [x] Raises documentation
- [x] See Also cross-references
- [x] No nested triple-quotes
- [x] Proper indentation
- [x] No trailing whitespace

---

*This is a living document - updated as enhancements progress*



