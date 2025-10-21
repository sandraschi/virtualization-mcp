# Tool Mode Configuration Guide

**Purpose:** Switch between production (5 tools) and testing (60+ tools) modes

---

## Overview

virtualization-mcp supports two tool registration modes to balance usability and functionality:

### Production Mode (Default)
- **Tools:** 5 portmanteau tools only
- **Benefits:** Clean, organized tool list for Claude Desktop
- **Best For:** End users, production deployments

### Testing Mode
- **Tools:** 60+ tools (portmanteau + all individual tools)
- **Benefits:** Access to every individual operation
- **Best For:** Development, testing, debugging

---

## Configuration

### Method 1: Environment Variable (Recommended)

Set the `TOOL_MODE` environment variable:

**Production (5 tools):**
```bash
export TOOL_MODE=production
```

**Testing (60+ tools):**
```bash
export TOOL_MODE=testing
# Or
export TOOL_MODE=all
```

### Method 2: MCP Config File

Edit your Claude Desktop config file:

**Production Config (`mcp_config.json`):**
```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/virtualization-mcp", "run", "virtualization-mcp"],
      "env": {
        "TOOL_MODE": "production"
      }
    }
  }
}
```

**Testing Config (`mcp_config.testing.json`):**
```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/virtualization-mcp", "run", "virtualization-mcp"],
      "env": {
        "TOOL_MODE": "testing"
      }
    }
  }
}
```

### Method 3: Code Configuration

Modify `src/virtualization_mcp/config.py`:

```python
class Settings(BaseSettings):
    # ...
    TOOL_MODE: str = "production"  # Change to "testing" for all tools
```

---

## Tool Lists

### Production Mode (5-6 Tools):

1. **vm_management**
   - 10 sub-operations: list, create, start, stop, delete, clone, reset, pause, resume, info

2. **network_management**
   - 5 sub-operations: list_networks, create_network, remove_network, list_adapters, configure_adapter

3. **snapshot_management**
   - 4 sub-operations: list, create, restore, delete

4. **storage_management**
   - 6 sub-operations: list_controllers, create_controller, remove_controller, list_disks, create_disk, attach_disk

5. **system_management**
   - 5 sub-operations: host_info, vbox_version, ostypes, metrics, screenshot

6. **hyperv_management** (Windows only)
   - 4 sub-operations: list, get, start, stop

**Total:** 5 tools (6 on Windows), 30 sub-operations

**Tool Discovery:** MCP protocol provides `tools/list` method natively - use that instead of custom discovery tools!

### Testing Mode (60+ Tools):

**All production tools PLUS:**

**VM Tools (11):**
- list_vms, get_vm_info, start_vm, stop_vm, create_vm, delete_vm, clone_vm, reset_vm, pause_vm, resume_vm, modify_vm

**Storage Tools (6):**
- list_storage_controllers, create_storage_controller, remove_storage_controller, create_disk, attach_disk, etc.

**Network Tools (5):**
- list_hostonly_networks, create_hostonly_network, remove_hostonly_network, configure_network_adapter, etc.

**Snapshot Tools (4):**
- list_snapshots, create_snapshot, restore_snapshot, delete_snapshot

**System Tools (5):**
- get_system_info, get_vbox_version, list_ostypes, get_vm_metrics, get_vm_screenshot

**Backup Tools (3):**
- create_vm_backup, list_vm_backups, delete_vm_backup

**Discovery Tools (3):**
- list_tools, get_tool_info, get_tool_schema

**Example Tools (3):**
- example_greet, get_counter, analyze_file

**Plus:** All portmanteau tools from production mode

**Total:** 60+ tools

---

## When to Use Each Mode

### Use Production Mode When:
- ✅ Deploying to end users
- ✅ Using in Claude Desktop for daily work
- ✅ Want clean, organized tool list
- ✅ Portmanteau tools provide all needed functionality
- ✅ Prefer action-based interface (e.g., `vm_management(action="start", vm_name="MyVM")`)

### Use Testing Mode When:
- ✅ Developing new features
- ✅ Testing individual tool functions
- ✅ Debugging specific operations
- ✅ Comparing portmanteau vs individual tool behavior
- ✅ Need direct access to underlying functions

---

## Switching Modes

### Quick Switch with Environment Variable:

**Windows (PowerShell):**
```powershell
# Production
$env:TOOL_MODE = "production"

# Testing
$env:TOOL_MODE = "testing"
```

**Linux/Mac (Bash):**
```bash
# Production
export TOOL_MODE=production

# Testing  
export TOOL_MODE=testing
```

**Then restart the MCP server or Claude Desktop**

### Permanent Switch in Config:

Edit your `mcp_config.json` and restart Claude Desktop.

---

## Verification

### Check Current Mode:

When the server starts, check the logs:

**Production Mode:**
```
Tool mode: production - Using portmanteau tools only (production mode)
Portmanteau tools registered successfully
```

**Testing Mode:**
```
Tool mode: testing - Registering individual tools for testing
Portmanteau tools registered successfully
Individual tools registered successfully (testing mode)
```

### Test in Claude Desktop:

Ask Claude: **"List all your available tools"**

**Production Mode Response:**
- 5 portmanteau tools shown
- Clean, organized list

**Testing Mode Response:**
- 60+ tools shown
- Both portmanteau and individual tools

---

## Example Configurations

### Example 1: Production User

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": ["--directory", "/home/user/virtualization-mcp", "run", "virtualization-mcp"],
      "env": {
        "TOOL_MODE": "production",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Result:** Clean 5-tool interface

### Example 2: Developer Testing

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": ["--directory", "/home/dev/virtualization-mcp", "run", "virtualization-mcp"],
      "env": {
        "TOOL_MODE": "testing",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true"
      }
    }
  }
}
```

**Result:** All 60+ tools available with debug logging

### Example 3: CI/CD Testing

```yaml
# In GitHub Actions
env:
  TOOL_MODE: testing
  DEBUG: true
```

---

## Benefits

### Production Mode:
- ✅ Cleaner tool list for Claude
- ✅ Easier for users to discover capabilities
- ✅ Action-based interface more intuitive
- ✅ Reduced cognitive load
- ✅ Professional appearance

### Testing Mode:
- ✅ Direct access to all functions
- ✅ Easier to test specific operations
- ✅ Better for debugging
- ✅ Backward compatibility maintained
- ✅ More granular control

---

## Default Configuration

**Out of the box:** `TOOL_MODE = "production"`

**Rationale:**
- End users get clean interface
- Portmanteau tools cover all use cases
- Can switch to testing mode anytime
- Better first impression

---

## Troubleshooting

### "I don't see individual tools in Claude"

**Answer:** You're in production mode. Set `TOOL_MODE=testing` and restart.

### "Too many tools, overwhelming"

**Answer:** You're in testing mode. Set `TOOL_MODE=production` (or remove the env var) and restart.

### "Tools not changing after setting TOOL_MODE"

**Answer:** Restart Claude Desktop to reload the MCP server with new config.

---

## File Locations

**Config Files:**
- `mcp_config.json` - Production config (TOOL_MODE=production)
- `mcp_config.testing.json` - Testing config (TOOL_MODE=testing)
- `src/virtualization_mcp/config.py` - Default TOOL_MODE setting

**Registration Code:**
- `src/virtualization_mcp/tools/register_tools.py` - Tool registration logic
- `src/virtualization_mcp/all_tools_server.py` - Server initialization

---

## Summary

The `TOOL_MODE` configuration provides flexible tool registration:
- **Production:** 5 clean portmanteau tools (default)
- **Testing:** 60+ tools for development

Switch anytime with environment variable or config file!

**Default:** Production mode for best user experience ✨

