# MCP Portmanteau Best Practices - Discoverability Pattern

**For:** MCP Server Developers  
**Topic:** Portmanteau tool design for optimal client discoverability  
**Discovered In:** virtualization-mcp v1.0.1b2 development  
**Importance:** CRITICAL

---

## The Discoverability Principle

**MCP clients (like Claude Desktop) must discover ALL available operations at startup via the JSON schema, not by reading docstrings or calling tools.**

---

## ❌ The Wrong Way (Breaks Discoverability)

```python
@mcp.tool()
async def vm_management(
    action: str,  # ← Generic string - no enum in schema!
    vm_name: str | None = None
) -> dict:
    '''
    Manage VMs. Available actions: list, create, start, stop, delete
    
    (Documentation is good, but schema doesn't include enum!)
    '''
    if action == "list":
        return list_all_vms()
    elif action == "create":
        return create_vm(vm_name)
    # ...
```

### What MCP Client Sees:

```json
{
  "name": "vm_management",
  "inputSchema": {
    "properties": {
      "action": {
        "type": "string"  // ← No enum! Client can't discover valid actions!
      }
    }
  }
}
```

### User Experience:

```
User: "What can you do with VMs?"
Claude: "I have a vm_management tool, but I'm not sure what specific 
         operations it supports. Let me try to find out..."
```

---

## ✅ The Right Way (Perfect Discoverability)

```python
from typing import Literal

@mcp.tool()
async def vm_management(
    action: Literal["list", "create", "start", "stop", "delete"],  # ← Explicit enum!
    vm_name: str | None = None
) -> dict:
    '''
    Manage virtual machines with various actions.
    
    Args:
        action: The operation to perform:
            - list: List all VMs with their current states
            - create: Create a new VM with specified configuration
            - start: Start a VM (headless or GUI mode)
            - stop: Stop a running VM (graceful or forced)
            - delete: Delete a VM and optionally its files
            
        vm_name: Name of the virtual machine (required for most actions)
        
    Returns:
        Dict with success status and operation results
        
    Examples:
        # List all VMs
        await vm_management(action="list")
        
        # Start a specific VM
        await vm_management(action="start", vm_name="my-vm")
    '''
    if action == "list":
        return list_all_vms()
    elif action == "create":
        return create_vm(vm_name)
    # ...
```

### What MCP Client Sees:

```json
{
  "name": "vm_management",
  "inputSchema": {
    "properties": {
      "action": {
        "type": "string",
        "enum": ["list", "create", "start", "stop", "delete"]  // ← Perfect!
      }
    }
  }
}
```

### User Experience:

```
User: "What can you do with VMs?"
Claude: "I can help you with VM management including:
         - list: List all virtual machines
         - create: Create a new VM
         - start: Start a VM
         - stop: Stop a running VM
         - delete: Delete a VM
         
         What would you like to do?"
```

---

## Complete Pattern

### Recommended Structure:

```python
from typing import Any, Literal
from fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

# 1. Define actions dictionary (for validation and error messages)
ACTIONS = {
    "list": "List all items",
    "create": "Create a new item",
    "start": "Start an item",
    "stop": "Stop an item",
    "delete": "Delete an item",
}

# 2. Create Literal type (optional, for reuse)
ActionType = Literal["list", "create", "start", "stop", "delete"]

def register_portmanteau_tool(mcp: FastMCP) -> None:
    """Register the portmanteau tool."""

    # 3. Use Literal in function signature
    @mcp.tool()
    async def portmanteau_management(
        action: ActionType,  # ← Discoverable via schema enum!
        item_name: str | None = None,
        # ... other parameters
    ) -> dict[str, Any]:
        '''
        Comprehensive description of the portmanteau tool.
        
        Args:
            action: The operation to perform. Available actions:
                - list: Detailed description with requirements
                - create: Detailed description with requirements
                - start: Detailed description with requirements
                - stop: Detailed description with requirements
                - delete: Detailed description with requirements
                
            item_name: Name of the item (required for most actions)
            
        Returns:
            Dictionary containing:
            - success: bool - Operation success status
            - action: str - Action that was performed
            - result: Any - Operation results
            - error: str - Error message if failed
            
        Examples:
            # List all items
            result = await portmanteau_management(action="list")
            
            # Create an item
            result = await portmanteau_management(
                action="create",
                item_name="my-item"
            )
            
            # Start an item
            result = await portmanteau_management(
                action="start",
                item_name="my-item"
            )
        '''
        try:
            # 4. Validate action against dictionary
            if action not in ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'",
                    "available_actions": ACTIONS,
                }
            
            logger.info(f"Executing portmanteau action: {action}")
            
            # 5. Route to action handlers
            if action == "list":
                return await _handle_list()
            elif action == "create":
                return await _handle_create(item_name)
            # ... etc
            
        except Exception as e:
            logger.error(f"Portmanteau error for action '{action}': {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action,
            }
```

---

## Additional Discoverable Parameters

### Apply Literal Types to ALL Constrained Parameters:

```python
async def vm_management(
    action: Literal["list", "create", ...],  # ← Operations
    vm_name: str | None = None,
    network_type: Literal["nat", "bridged", "hostonly"] | None = None,  # ← Network modes
    state_filter: Literal["running", "poweroff", "paused"] | None = None,  # ← States
    disk_format: Literal["vdi", "vmdk", "vhd"] | None = None,  # ← Formats
):
```

**Each Literal becomes an enum in the schema!**

---

## Testing Discoverability

### 1. Inspect Generated Schema

```python
# After registering tools
from fastmcp import FastMCP

mcp = FastMCP("test-server")
register_your_tools(mcp)

# FastMCP generates MCP-compliant schemas
# Verify enums are present
```

### 2. Test in MCP Client

**Start the server**, then:
- Ask Claude: "List all your available tools"
- Ask Claude: "What operations does vm_management support?"
- Verify Claude lists specific enumerated actions

### 3. Check MCP Protocol Messages

Enable debug logging to see MCP initialization:
- Tools/list response should include inputSchema
- inputSchema should have enum arrays for Literal parameters

---

## Common Mistakes

### Mistake 1: Forgetting Literal

```python
action: str  # ❌ No discoverability
```

**Fix:**
```python
action: Literal["list", "create", ...]  # ✅ Discoverable
```

### Mistake 2: Outdated Literal Values

```python
action: Literal["list", "create"]  # ← Only 2 values

# But implementation has:
if action == "list": ...
elif action == "create": ...
elif action == "start": ...  # ← Missing from Literal!
```

**Fix:** Keep Literal synchronized with implementation

### Mistake 3: Only Documenting in Docstring

```python
action: str  # ❌ 
'''
action can be: list, create, start  # ← Not in schema!
'''
```

**Fix:** Use Literal + document in docstring (both!)

---

## FastMCP-Specific Notes

### How FastMCP Generates Schemas:

1. Reads function signature type hints
2. Converts Python types to JSON Schema types
3. `Literal["a", "b"]` → `{"enum": ["a", "b"]}`
4. Sends schema to MCP client via protocol

### FastMCP 2.12+ Features:

- Automatic docstring extraction (if no description parameter)
- Type hint → JSON schema conversion
- Literal support for enums
- Optional/required parameter detection

---

## Summary

### The Golden Rule:

**For every action/operation parameter in a portmanteau MCP tool, use `Literal` types with all valid values explicitly enumerated.**

### Why It Matters:

- MCP clients discover operations via schema (not docstrings)
- Schema enums enable client-side understanding
- Better user experience in Claude Desktop
- Fundamental MCP protocol best practice

### Implementation:

1. Import: `from typing import Literal`
2. Define: `action: Literal["op1", "op2", "op3"]`
3. Document: In docstring too
4. Validate: Against action dict
5. Test: Verify in Claude Desktop

---

## References

- **MCP Specification:** https://modelcontextprotocol.io/docs
- **FastMCP:** https://github.com/jlowin/fastmcp
- **Python Literal:** https://docs.python.org/3/library/typing.html#typing.Literal
- **JSON Schema Enums:** https://json-schema.org/understanding-json-schema/reference/enum

---

**Status:** Best practice documented and implemented in virtualization-mcp ✅

