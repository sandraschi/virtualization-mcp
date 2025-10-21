# Tool Mode Quick Reference

## 🎯 Production Mode (Default) - 6-7 Tools

**For:** End users, Claude Desktop  
**Setting:** `TOOL_MODE=production` (or omit - this is default)

**Tools Registered:**
1. vm_management (10 operations)
2. network_management (5 operations)
3. snapshot_management (4 operations)
4. storage_management (6 operations)
5. system_management (5 operations)
6. discovery_management (3 operations)
7. hyperv_management (4 operations, Windows only)

**Example:**
```
"Start the VM named MyVM"
→ Claude uses: vm_management(action="start", vm_name="MyVM")
```

---

## 🔧 Testing Mode - 60+ Tools

**For:** Developers, testing, debugging  
**Setting:** `TOOL_MODE=testing`

**Tools Registered:**
- All 5 portmanteau tools
- PLUS 55+ individual tools (list_vms, create_vm, start_vm, etc.)

**Example:**
```
"Start the VM named MyVM"
→ Claude can use: vm_management(action="start") OR start_vm(vm_name="MyVM")
```

---

## ⚡ Quick Switch

### In mcp_config.json:
```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "env": {
        "TOOL_MODE": "production"
      }
    }
  }
}
```

Change to `"testing"` and restart Claude Desktop.

### Or use the testing config:
```bash
# Copy testing config
cp mcp_config.testing.json ~/.config/Claude/mcp_config.json

# Restart Claude Desktop
```

---

## 📋 When to Use Each

| Scenario | Mode | Why |
|----------|------|-----|
| Daily VM management | Production | Clean, simple interface |
| End user deployment | Production | Professional UX |
| Developing new features | Testing | Access all functions |
| Debugging issues | Testing | Granular control |
| Testing portmanteau | Testing | Compare behaviors |
| CI/CD testing | Testing | Test all code paths |

---

**Default: Production** for best user experience!

Full documentation: `docs/mcp-technical/TOOL_MODE_CONFIGURATION.md`

