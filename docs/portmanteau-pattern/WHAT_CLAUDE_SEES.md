# What Claude Desktop Sees - Portmanteau Discoverability

## When You Ask: "List virtualization tools"

### Claude's Response Will Be:

**"I have access to 6 virtualization management tools (7 on Windows):**

**1. vm_management** - Virtual machine lifecycle management with 10 operations:
- list: List all VMs
- create: Create a new VM
- start: Start a VM
- stop: Stop a VM
- delete: Delete a VM
- clone: Clone a VM
- reset: Reset a VM
- pause: Pause a VM
- resume: Resume a paused VM
- info: Get detailed VM information

**2. network_management** - Network configuration with 5 operations:
- list_networks: List all host-only networks
- create_network: Create a host-only network
- remove_network: Remove a host-only network
- list_adapters: List network adapters for a VM
- configure_adapter: Configure network adapter for a VM

**3. snapshot_management** - Snapshot operations with 4 operations:
- list: List all snapshots for a VM
- create: Create a snapshot of a VM
- restore: Restore a VM to a snapshot
- delete: Delete a snapshot

**4. storage_management** - Storage and disk management with 6 operations:
- list_controllers: List storage controllers
- create_controller: Create a storage controller
- remove_controller: Remove a storage controller
- list_disks: List virtual disks
- create_disk: Create a new virtual disk
- attach_disk: Attach a disk to a VM

**5. system_management** - System information with 5 operations:
- host_info: Get host system information
- vbox_version: Get VirtualBox version
- ostypes: List available OS types
- metrics: Get VM performance metrics
- screenshot: Take a screenshot of a running VM

**6. discovery_management** - Help and tool information with 4 operations:
- list_tools: List all available tools
- tool_info: Get detailed tool information
- tool_schema: Get JSON schema for a tool
- help: Get general help

**7. hyperv_management** (Windows only) - Hyper-V VM management with 4 operations:
- list: List all Hyper-V VMs
- get: Get detailed Hyper-V VM info
- start: Start a Hyper-V VM
- stop: Stop a Hyper-V VM

---

## How Claude Discovers This

### At Startup (MCP Protocol):

1. **Server starts** → Registers 6-7 portmanteau tools
2. **FastMCP generates schemas** from type hints:
   ```json
   {
     "name": "vm_management",
     "inputSchema": {
       "properties": {
         "action": {
           "type": "string",
           "enum": ["list", "create", "start", "stop", "delete", "clone", "reset", "pause", "resume", "info"]
         }
       }
     },
     "description": "Manage virtual machines with various actions..."
   }
   ```

3. **MCP sends schemas to Claude** via tools/list protocol method

4. **Claude parses schemas** and extracts:
   - Tool names
   - Action enums from Literal types
   - Parameter requirements
   - Docstring descriptions

5. **Claude builds understanding** of ALL 33 operations without calling any tools!

---

## The Key: Literal Types

### This Code:
```python
action: Literal["list", "create", "start", "stop", "delete", ...]
```

### Becomes This Schema:
```json
{
  "action": {
    "type": "string",
    "enum": ["list", "create", "start", "stop", "delete", ...]
  }
}
```

### Which Tells Claude:
"The vm_management tool has an action parameter with these exact valid values: list, create, start, stop, delete..."

---

## Complete Discoverability

**Claude knows at startup (WITHOUT calling any tools):**

✅ 6-7 tool names  
✅ ALL 33 sub-operations (from action enums)  
✅ Parameter requirements (from function signatures)  
✅ Return types (from type hints)  
✅ Detailed descriptions (from docstrings)  
✅ Usage examples (from docstrings)  

**No extra search steps needed!**

---

## Try It!

Ask Claude in a conversation:

**"What can you do with virtual machines?"**

Claude should respond with:
- All 10 vm_management operations listed
- Brief description of each
- No uncertainty, complete understanding

**"How do I create a VM?"**

Claude should respond with:
- Use vm_management with action="create"
- Required parameters: vm_name, os_type, memory_mb, disk_size_gb
- Example call
- No guessing!

---

**Status:** Full sub-tool discoverability via Literal types + comprehensive docstrings ✅

