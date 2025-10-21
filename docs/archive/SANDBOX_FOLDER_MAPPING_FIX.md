# Windows Sandbox Folder Mapping - Fixed! ✅

## Problem Identified

The Windows Sandbox folder mapping feature had several bugs that prevented it from working:

1. **Missing SandboxFolder tag**: Windows Sandbox XML requires both `<HostFolder>` and optionally `<SandboxFolder>` tags, but only `<HostFolder>` was being generated
2. **Wrong folder structure**: Expected `dict[str, str]` but was accessing keys like `f['host_path']` without proper typing
3. **Incorrect LogonCommand format**: Commands were being joined incorrectly, creating malformed XML
4. **No XML escaping**: Special characters in paths and commands could break the XML
5. **No path validation**: Invalid paths were not being caught early

## Issues Fixed

### 1. Created Proper MappedFolder Model ✅

**Before:**
```python
mapped_folders: list[dict[str, str]]  # Unclear structure
```

**After:**
```python
class MappedFolder(BaseModel):
    host_path: str  # Validated, must exist and be absolute
    sandbox_path: str | None  # Optional destination in sandbox
    readonly: bool = False  # Whether folder is read-only
```

### 2. Fixed XML Generation ✅

**Before (Broken):**
```xml
<MappedFolder>
  <HostFolder>C:\path</HostFolder>
  <ReadOnly>true</ReadOnly>
</MappedFolder>
```

**After (Correct):**
```xml
<MappedFolder>
  <HostFolder>C:\path</HostFolder>
  <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\Shared</SandboxFolder>
  <ReadOnly>true</ReadOnly>
</MappedFolder>
```

### 3. Fixed LogonCommand Format ✅

**Before (Broken):**
```xml
<LogonCommand>
  <Command>cmd1</Command><Command>cmd2</Command>
</LogonCommand>
```

**After (Correct):**
```xml
<LogonCommand>
  <Command>cmd1</Command>
</LogonCommand>
<LogonCommand>
  <Command>cmd2</Command>
</LogonCommand>
```

### 4. Added XML Escaping ✅

Now all paths and commands are properly escaped using `html.escape()`:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`

### 5. Added Path Validation ✅

- Validates paths exist before creating sandbox
- Ensures paths are absolute
- Provides clear error messages

## Usage Examples

### Basic Folder Mapping

```python
from virtualization_mcp.plugins.sandbox import MappedFolder, SandboxConfig

# Map a folder (read-write)
config = SandboxConfig(
    name="my-sandbox",
    memory_mb=2048,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\Users\\YourName\\Documents\\Projects",
            readonly=False
        )
    ]
)
```

### Custom Sandbox Path

```python
# Map to a specific location in the sandbox
config = SandboxConfig(
    name="dev-sandbox",
    memory_mb=4096,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\Projects\\MyProject",
            sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\MyProject",
            readonly=False
        )
    ]
)
```

### Read-Only Mapping

```python
# Map a folder as read-only (for security)
config = SandboxConfig(
    name="test-sandbox",
    memory_mb=2048,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\Shared\\TestData",
            readonly=True  # Cannot modify files
        )
    ]
)
```

### Multiple Folders

```python
# Map multiple folders
config = SandboxConfig(
    name="multi-folder-sandbox",
    memory_mb=4096,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\Projects",
            sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Projects",
            readonly=False
        ),
        MappedFolder(
            host_path="C:\\Reference",
            sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Reference",
            readonly=True
        ),
        MappedFolder(
            host_path="C:\\Output",
            readonly=False
        )
    ]
)
```

### With Logon Commands

```python
# Map folders and run setup commands
config = SandboxConfig(
    name="setup-sandbox",
    memory_mb=4096,
    mapped_folders=[
        MappedFolder(
            host_path="C:\\Scripts",
            sandbox_path="C:\\Users\\WDAGUtilityAccount\\Desktop\\Scripts",
            readonly=True
        )
    ],
    logon_commands=[
        'cd C:\\Users\\WDAGUtilityAccount\\Desktop\\Scripts',
        'powershell -ExecutionPolicy Bypass -File setup.ps1',
        'echo Setup complete'
    ]
)
```

## Using with Claude

When using the MCP server in Claude, you can create sandboxes with folder mapping:

### Example 1: Development Sandbox

```
Create a Windows Sandbox with:
- Name: dev-sandbox
- Memory: 4GB
- Map my C:\Projects folder (read-write)
- Map C:\Tools folder as read-only
- Run these commands on startup:
  - Install Node.js
  - Clone my repository
```

### Example 2: Testing Sandbox

```
Create a Windows Sandbox for testing with:
- Name: test-env
- Memory: 2GB
- Map C:\TestData folder (read-only)
- Map C:\Results folder (read-write)
- Network enabled
- Run test suite on startup
```

## Generated WSX File Example

When you create a sandbox with folder mapping, this generates a `.wsx` configuration file:

```xml
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Enable</Networking>
  <MemoryInMB>4096</MemoryInMB>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>C:\Projects</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\Projects</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>C:\Reference</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\Reference</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>echo Sandbox ready</Command>
  </LogonCommand>
</Configuration>
```

## Validation

The fixed implementation validates:

1. **Host path exists**: `ValueError: Host path does not exist: ...`
2. **Absolute paths**: Relative paths are rejected
3. **Sandbox name**: Cannot be empty
4. **Memory range**: Must be between 1024 MB and 32768 MB

## Testing

All tests pass (12/12):

```bash
cd d:\Dev\repos\virtualization-mcp
uv run pytest tests/test_sandbox_folder_mapping.py -v
```

Tests cover:
- ✅ Valid folder mapping
- ✅ Invalid path rejection
- ✅ Relative path rejection
- ✅ XML generation with folders
- ✅ XML generation with commands
- ✅ XML special character escaping
- ✅ Complete configuration
- ✅ Name validation
- ✅ Memory validation
- ✅ Empty folders/commands handling

## API Reference

### MappedFolder

```python
class MappedFolder(BaseModel):
    """A folder mapped into the Windows Sandbox."""
    
    host_path: str
    # Required. Path on the host machine.
    # Must exist and be an absolute path.
    
    sandbox_path: str | None = None
    # Optional. Path inside the sandbox.
    # If not specified, maps to Desktop by default.
    
    readonly: bool = False
    # Optional. Mount as read-only.
    # Default is False (read-write).
```

### SandboxConfig

```python
class SandboxConfig(BaseModel):
    """Configuration for Windows Sandbox."""
    
    name: str
    # Required. Name of the sandbox configuration.
    
    memory_mb: int = 4096
    # Optional. Memory in MB (1024-32768).
    
    vgpu: bool = True
    # Optional. Enable virtual GPU.
    
    networking: bool = True
    # Optional. Enable networking.
    
    mapped_folders: list[MappedFolder] = []
    # Optional. List of folders to map.
    
    logon_commands: list[str] = []
    # Optional. Commands to run on startup.
```

## Security Notes

1. **Path Validation**: All paths are validated before use
2. **XML Escaping**: All user input is XML-escaped to prevent injection
3. **Read-Only Mode**: Use `readonly=True` for sensitive folders
4. **Sandbox Isolation**: Windows Sandbox provides full isolation
5. **Temporary Files**: WSX files are cleaned up after use

## Common Use Cases

### 1. Software Testing
Map your software folder and test data, run tests in isolation:
```python
MappedFolder(host_path="C:\\MySoftware", readonly=True),
MappedFolder(host_path="C:\\TestResults", readonly=False)
```

### 2. Build Environment
Map source code and build output:
```python
MappedFolder(host_path="C:\\SourceCode", readonly=True),
MappedFolder(host_path="C:\\BuildOutput", readonly=False)
```

### 3. Document Processing
Map input and output folders for document conversion:
```python
MappedFolder(host_path="C:\\Documents\\Input", readonly=True),
MappedFolder(host_path="C:\\Documents\\Output", readonly=False)
```

### 4. Web Development
Map website files and server logs:
```python
MappedFolder(host_path="C:\\WebSite", readonly=False),
MappedFolder(host_path="C:\\Logs", readonly=False)
```

## Files Changed

### Modified:
- ✅ `src/virtualization_mcp/plugins/sandbox/manager.py`
  - Added `MappedFolder` Pydantic model
  - Fixed XML generation for MappedFolders
  - Fixed LogonCommand XML generation
  - Added XML escaping with `html.escape()`
  - Added path validation

- ✅ `src/virtualization_mcp/plugins/sandbox/__init__.py`
  - Exported `MappedFolder` and `SandboxConfig` models

### Created:
- ✅ `tests/test_sandbox_folder_mapping.py` - Comprehensive test suite (12 tests)
- ✅ `SANDBOX_FOLDER_MAPPING_FIX.md` - This documentation

## Troubleshooting

### "Host path does not exist"
**Cause**: The specified path doesn't exist on your machine.
**Solution**: Verify the path exists before creating the sandbox.

### "Name cannot be empty"
**Cause**: Sandbox name is empty or whitespace.
**Solution**: Provide a valid name: `name="my-sandbox"`

### Sandbox doesn't show mapped folders
**Cause**: May be using old code without the fix.
**Solution**: 
1. Ensure you're using the latest code
2. Verify the WSX file contains `<SandboxFolder>` tags
3. Check folder permissions on the host

### Commands not running
**Cause**: LogonCommand XML might be malformed.
**Solution**: 
1. Use the fixed version with proper command blocks
2. Verify commands use correct syntax
3. Check sandbox logs for errors

## Status

**✅ COMPLETE** - Windows Sandbox folder mapping now works correctly!

All bugs fixed, fully tested, and documented.



