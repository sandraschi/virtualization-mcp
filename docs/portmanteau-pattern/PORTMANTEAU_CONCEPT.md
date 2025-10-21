# The Portmanteau Pattern for MCP Servers

**For:** MCP Server Developers  
**Problem:** Tool explosion in feature-rich MCP servers  
**Solution:** Portmanteau tools (action-based consolidation)  
**Example Implementation:** virtualization-mcp

---

## The Problem: Tool Explosion

### Scenario: VirtualBox Management MCP Server

**Naive approach - Individual tools:**
- list_vms
- get_vm_info
- create_vm
- start_vm
- stop_vm
- pause_vm
- resume_vm
- reset_vm
- delete_vm
- clone_vm
- modify_vm
- get_vm_state
- get_vm_metrics
- list_snapshots
- create_snapshot
- restore_snapshot
- delete_snapshot
- list_storage_controllers
- create_storage_controller
- remove_storage_controller
- create_disk
- attach_disk
- list_hostonly_networks
- create_hostonly_network
- remove_hostonly_network
- configure_network_adapter
- ... (60+ more tools)

**Result:** 
- 💥 Tool list overwhelming for users
- 🤯 Cognitive overload in Claude Desktop
- 📊 Difficult to discover related operations
- 🔍 Hard to understand what's available
- 📱 Poor mobile/UI experience

### Real User Experience:

```
User: "What can you do with VMs?"

Claude: "I have access to:
- list_vms
- get_vm_info
- create_vm
- start_vm
- stop_vm
- pause_vm
... (60 more lines)

It's overwhelming - what do you specifically need?"
```

---

## The Solution: Portmanteau Tools

### Definition

**Portmanteau Tool:** A single MCP tool that consolidates multiple related operations through an action-based interface.

**Pattern:**
```python
@mcp.tool()
async def category_management(
    action: Literal["operation1", "operation2", "operation3"],
    ...parameters...
) -> dict:
    '''
    Comprehensive tool managing all category operations.
    
    Available operations:
    - operation1: Description
    - operation2: Description
    - operation3: Description
    '''
    if action == "operation1":
        return handle_operation1()
    elif action == "operation2":
        return handle_operation2()
    # ...
```

### virtualization-mcp Implementation

**Before (60+ individual tools):**
- list_vms, create_vm, start_vm, stop_vm, delete_vm, clone_vm, ...
- list_snapshots, create_snapshot, restore_snapshot, delete_snapshot, ...
- list_storage_controllers, create_storage_controller, ...
- ... 60+ total tools

**After (6-7 portmanteau tools):**

1. **vm_management** (consolidates 10 VM tools)
2. **network_management** (consolidates 5 network tools)
3. **snapshot_management** (consolidates 4 snapshot tools)
4. **storage_management** (consolidates 6 storage tools)
5. **system_management** (consolidates 5 system tools)
6. **discovery_management** (consolidates 4 help/info tools)
7. **hyperv_management** (consolidates 4 Hyper-V tools, Windows only)

**Result:** 60+ tools → 6-7 clean portmanteau tools (with same 60+ operations)

### User Experience After:

```
User: "What can you do with VMs?"

Claude: "I can help with VM management through vm_management tool:
- list: List all VMs with details
- create: Create a new VM
- start: Start a VM
- stop: Stop a VM
- delete: Delete a VM
- clone: Clone a VM
- reset: Reset a VM
- pause: Pause a VM
- resume: Resume a paused VM
- info: Get detailed VM information

What would you like to do?"
```

**Much cleaner!**

---

## When to Use Portmanteau Pattern

### ✅ Use Portmanteau When:

1. **You have 10+ related tools**
   - Example: VM lifecycle operations
   - Pattern: Group by category (vm, network, storage, etc.)

2. **Operations are conceptually related**
   - Example: All snapshot operations (create, restore, delete, list)
   - Pattern: One portmanteau per logical category

3. **Users think in categories, not individual functions**
   - User thinks: "VM management"
   - Not: "I need list_vms, then start_vm, then..."

4. **Tool explosion hurts UX**
   - More than ~15-20 tools = overwhelming
   - Portmanteau brings it down to 5-10 logical categories

5. **Operations share common parameters**
   - Most VM operations need `vm_name`
   - Makes sense to group them

### ❌ Don't Use Portmanteau When:

1. **You only have 5-10 tools total**
   - Not worth the complexity
   - Individual tools are fine

2. **Operations are completely unrelated**
   - Don't force-fit into portmanteau
   - Example: vm_operation + email_sender = bad grouping

3. **Each operation has wildly different parameters**
   - Portmanteau works best with overlapping parameters
   - Too many optional parameters = confusing

4. **Users expect individual tools**
   - Some domains prefer granular tools
   - Consider your user base

---

## Implementation in virtualization-mcp

### File Structure:

```
src/virtualization_mcp/tools/
├── portmanteau/
│   ├── __init__.py                    # Registers all portmanteau tools
│   ├── vm_management.py               # VM lifecycle (10 ops)
│   ├── network_management.py          # Networks (5 ops)
│   ├── snapshot_management.py         # Snapshots (4 ops)
│   ├── storage_management.py          # Storage (6 ops)
│   ├── system_management.py           # System info (5 ops)
│   ├── discovery_management.py        # Help/info (4 ops)
│   └── hyperv_management.py           # Hyper-V (4 ops, Windows)
├── vm/
│   └── vm_tools.py                    # Individual VM functions
├── network/
│   └── network_tools.py               # Individual network functions
├── snapshot/
│   └── snapshot_tools.py              # Individual snapshot functions
└── register_tools.py                  # Tool mode selector
```

### Pattern: Portmanteau Wraps Individual Tools

**Individual function:**
```python
# vm_tools.py
async def start_vm(vm_name: str, start_type: str = "headless") -> dict:
    '''Start a virtual machine.'''
    # Implementation
```

**Portmanteau wrapper:**
```python
# vm_management.py
async def vm_management(
    action: Literal["start", ...],
    vm_name: str | None = None
) -> dict:
    '''Manage VMs with various actions...'''
    
    if action == "start":
        return await start_vm(vm_name=vm_name)  # ← Delegates to individual tool
```

**Benefits:**
- Individual tools remain for direct use (testing mode)
- Portmanteau provides clean interface (production mode)
- Switchable via TOOL_MODE setting
- Best of both worlds

---

## FastMCP 2.12 Compliance Requirements

### 1. Self-Registration Pattern ✅

**Correct:**
```python
def register_category_management_tool(mcp: FastMCP) -> None:
    '''Register the category management portmanteau tool.'''
    
    @mcp.tool()  # ← No description parameter!
    async def category_management(...):
        '''Comprehensive docstring...'''
        # Implementation
```

**Why:**
- FastMCP 2.12 extracts descriptions from docstrings
- Explicit `description` parameter OVERRIDES docstring
- Self-registration pattern keeps tools modular

### 2. Literal Types for Discoverability ✅

**Critical:**
```python
async def category_management(
    action: Literal["op1", "op2", "op3"],  # ← MUST have Literal!
    ...
):
```

**Why:**
- Literal types become JSON schema enums
- MCP clients discover valid actions at startup
- Without Literal, actions not discoverable
- This is THE fundamental requirement

### 3. Comprehensive Docstrings ✅

**Required sections:**
```python
'''
Brief description of the portmanteau.

Detailed explanation of purpose and scope.

Args:
    action: The operation to perform. Available actions:
        - op1: Detailed description with requirements
        - op2: Detailed description with requirements
        - op3: Detailed description with requirements
        (Document EVERY action!)
        
    param1: Parameter description with valid values
    param2: Parameter description with constraints
    
Returns:
    Dictionary containing:
    - success: bool - Status
    - result: Any - Operation results
    - error: str - Error if failed
    (Document complete structure!)
    
Examples:
    # Operation 1 example
    result = await category_management(action="op1")
    
    # Operation 2 example  
    result = await category_management(action="op2", param1="value")
    
    (Provide examples for EACH operation!)
'''
```

### 4. No Description Parameter ❌

**Wrong:**
```python
@mcp.tool(description="Manages categories")  # ❌ Overrides docstring!
```

**Right:**
```python
@mcp.tool()  # ✅ Uses docstring automatically
```

**Critical:** FastMCP 2.12 uses docstrings UNLESS you provide explicit description parameter which then OVERRIDES everything!

---

## Adding New Portmanteau Tools - Checklist

### Step 1: Plan the Portmanteau

- [ ] Identify 3+ related individual tools to consolidate
- [ ] Choose descriptive name: `{category}_management`
- [ ] List all operations (actions)
- [ ] Define shared parameters
- [ ] Decide on return value structure

### Step 2: Create the File

**Location:** `src/virtualization_mcp/tools/portmanteau/new_portmanteau.py`

**Template:**
```python
'''
{Category} Management Portmanteau Tool

Consolidates all {category}-related operations into a single tool.
Replaces {N} individual tools with one comprehensive interface.
'''

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Define available actions
ACTIONS = {
    "operation1": "Description of operation1",
    "operation2": "Description of operation2",
    # ... all operations
}


def register_{category}_management_tool(mcp: FastMCP) -> None:
    '''Register the {category} management portmanteau tool.'''

    @mcp.tool()  # ← No description parameter!
    async def {category}_management(
        action: Literal["operation1", "operation2", ...],  # ← MUST have Literal!
        # ... parameters ...
    ) -> dict[str, Any]:
        '''
        Comprehensive docstring documenting ALL operations.
        
        Args:
            action: Available operations:
                - operation1: Full description
                - operation2: Full description
                # ... document EVERY operation
        
        Returns:
            Dict with success, result, error
            
        Examples:
            # Example for each operation
        '''
        try:
            if action not in ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'",
                    "available_actions": ACTIONS,
                }
            
            # Route to handlers
            if action == "operation1":
                return await _handle_operation1()
            # ...
            
        except Exception as e:
            logger.error(f"Error in {category}_management: {e}")
            return {"success": False, "error": str(e)}


# Private handler functions
async def _handle_operation1() -> dict[str, Any]:
    '''Handle operation1 action.'''
    # Implementation or delegation to individual tool
    pass
```

### Step 3: Register in __init__.py

```python
# portmanteau/__init__.py
from .new_portmanteau import register_{category}_management_tool

def register_all_portmanteau_tools(mcp: FastMCP) -> None:
    # ... existing registrations ...
    register_{category}_management_tool(mcp)
```

### Step 4: Run Quality Checks

```bash
# Check imports
python -c "from virtualization_mcp.tools.portmanteau.new_portmanteau import register_{category}_management_tool; print('✅ Imports OK')"

# Run ruff
uv run ruff check src/virtualization_mcp/tools/portmanteau/new_portmanteau.py

# Auto-fix if needed
uv run ruff check --fix src/virtualization_mcp/tools/portmanteau/new_portmanteau.py

# Test registration
python -c "
from fastmcp import FastMCP
from virtualization_mcp.tools.portmanteau.new_portmanteau import register_{category}_management_tool

mcp = FastMCP('test')
register_{category}_management_tool(mcp)
print('✅ Registration OK')
"
```

### Step 5: Verify Discoverability

```python
# Check Literal type generates enum
import inspect
from virtualization_mcp.tools.portmanteau.new_portmanteau import register_{category}_management_tool

# Check signature has Literal
# Verify in Claude Desktop - ask about operations
```

---

## Common Traps and Pitfalls

### ❌ Trap 1: Forgetting Literal Type

**Problem:**
```python
async def category_management(action: str, ...):  # ❌
```

**Symptom:** Claude can't discover sub-operations at startup

**Fix:**
```python
async def category_management(action: Literal["op1", "op2"], ...):  # ✅
```

### ❌ Trap 2: Using description Parameter

**Problem:**
```python
@mcp.tool(description="Manages categories")  # ❌ Overrides docstring!
async def category_management(...):
    '''Detailed docstring with all operations...'''  # ← Never seen by Claude!
```

**Symptom:** Claude only sees short one-liner, no sub-operations

**Fix:**
```python
@mcp.tool()  # ✅ Uses docstring automatically
async def category_management(...):
    '''Detailed docstring...'''  # ← Claude sees this!
```

### ❌ Trap 3: Circular Import in Discovery/Help Tools

**Problem:**
```python
# In discovery portmanteau
from virtualization_mcp.all_tools_server import mcp  # ❌ Not exported!
```

**Symptom:** `ImportError: cannot import name 'mcp'`

**Fix:**
- Use static tool information (no imports)
- Or pass mcp instance as parameter
- Or use lazy imports

### ❌ Trap 4: Incomplete Docstrings

**Problem:**
```python
'''
Manages VMs.

Available actions: list, create, start, stop
'''  # ❌ Too brief!
```

**Symptom:** Claude doesn't understand parameter requirements or return values

**Fix:**
```python
'''
Manage virtual machines with various actions.

Args:
    action: Available operations:
        - list: List all VMs (no vm_name required)
        - create: Create VM (requires vm_name, os_type, memory_mb, disk_size_gb)
        # ... detailed for EACH operation
        
Returns:
    Dict with:
    - success: bool
    - result: Any
    # ... complete structure
    
Examples:
    # Example for each operation
'''
```

### ❌ Trap 5: Literal Out of Sync with Implementation

**Problem:**
```python
action: Literal["op1", "op2"]  # ← Only 2 listed

# But implementation has:
if action == "op1": ...
elif action == "op2": ...
elif action == "op3": ...  # ❌ Missing from Literal!
```

**Symptom:** Claude can't discover operation3, schema is incomplete

**Fix:** Keep Literal synchronized with ACTIONS dict and implementation

### ❌ Trap 6: Missing Error Handling

**Problem:**
```python
if action == "op1":
    return handle_op1()
# No else clause - what if invalid action?
```

**Symptom:** Confusing errors, poor UX

**Fix:**
```python
if action not in ACTIONS:
    return {
        "success": False,
        "error": f"Invalid action '{action}'",
        "available_actions": list(ACTIONS.keys())
    }
```

### ❌ Trap 7: Forgetting to Run Ruff

**Problem:** Code style inconsistencies, unused imports, formatting issues

**Fix:**
```bash
# Always run before committing
uv run ruff check --fix src/virtualization_mcp/tools/portmanteau/
```

---

## Universal Applicability

### When Your MCP Server Should Use Portmanteau Pattern:

✅ **Database Management** (20+ CRUD operations)
- Consolidate into: query_management, schema_management, data_management

✅ **File Operations** (30+ file tools)
- Consolidate into: file_management, directory_management, search_management

✅ **API Integration** (40+ endpoint tools)
- Consolidate into: users_management, posts_management, auth_management

✅ **Cloud Infrastructure** (50+ resource tools)
- Consolidate into: compute_management, storage_management, network_management

✅ **Any Domain with 15+ Related Tools**
- Group by logical categories
- 3-10 tools per portmanteau
- 5-10 portmanteau tools total

### Real-World Examples:

**AWS MCP Server:**
- ec2_management (instances, security groups, key pairs)
- s3_management (buckets, objects, policies)
- rds_management (databases, snapshots, backups)

**Git MCP Server:**
- repository_management (init, clone, remote)
- commit_management (commit, amend, revert)
- branch_management (create, delete, merge, checkout)

**Kubernetes MCP Server:**
- pod_management (create, delete, logs, exec)
- deployment_management (create, scale, rollback, update)
- service_management (create, expose, delete)

---

## Implementation Strategy

### Phase 1: Identify Tool Categories

1. List all existing/planned tools
2. Group by logical category (5-10 groups ideal)
3. Count tools per category (3-10 tools per group ideal)

### Phase 2: Design Portmanteau Structure

For each category:
1. Choose category name: `{category}_management`
2. List all operations (actions)
3. Identify shared parameters
4. Define return value structure
5. Plan error handling

### Phase 3: Implement Portmanteau Tools

For each portmanteau:
1. Create file in `tools/portmanteau/`
2. Follow template pattern
3. Use Literal types for actions
4. Write comprehensive docstring
5. Implement routing logic
6. Add error handling

### Phase 4: Register Tools

1. Import in `portmanteau/__init__.py`
2. Call registration function
3. Handle platform-specific tools (if any)
4. Log successful registration

### Phase 5: Testing & Validation

1. Check imports work
2. Run ruff for code quality
3. Test in FastMCP (tool registration)
4. Verify Literal generates enums
5. Test in Claude Desktop (actual usage)
6. Confirm all operations discoverable

---

## Tool Mode System (Production vs Testing)

### Dual-Mode Support:

**Production Mode (default):**
- Only portmanteau tools registered
- Clean 5-10 tool interface
- Best for end users

**Testing Mode:**
- Portmanteau + individual tools
- 60+ tools total
- Best for development

**Implementation:**
```python
def register_all_tools(mcp: FastMCP, tool_mode: str = "production"):
    # Always register portmanteau tools
    register_all_portmanteau_tools(mcp)
    
    # Register individual tools only in testing mode
    if tool_mode in ["testing", "all"]:
        _register_individual_tools(mcp)
```

**Configuration:**
```json
{
  "env": {
    "TOOL_MODE": "production"  // or "testing"
  }
}
```

---

## Maintenance

### When Adding New Operation to Existing Portmanteau:

1. **Add to ACTIONS dict:**
   ```python
   ACTIONS = {
       "existing_op": "...",
       "new_op": "New operation description",  # ← Add here
   }
   ```

2. **Add to Literal type:**
   ```python
   action: Literal["existing_op", "new_op"]  # ← Add here
   ```

3. **Document in docstring:**
   ```python
   '''
   Args:
       action: Operations:
           - existing_op: ...
           - new_op: Description  # ← Add here
   '''
   ```

4. **Add routing:**
   ```python
   elif action == "new_op":
       return await _handle_new_op()
   ```

5. **Run ruff:**
   ```bash
   uv run ruff check --fix src/virtualization_mcp/tools/portmanteau/
   ```

6. **Test:** Verify in Claude Desktop

---

## Quality Standards

### For Every Portmanteau Tool:

✅ **File header docstring** explaining what it consolidates  
✅ **ACTIONS dict** for validation and error messages  
✅ **Literal type** with all operations enumerated  
✅ **@mcp.tool()** with NO description parameter  
✅ **Comprehensive function docstring** with:
  - Purpose and scope
  - Every action documented in Args
  - All parameters explained with valid values
  - Return value structure
  - Examples for each operation (or most common ones)
✅ **Validation** of action against ACTIONS dict  
✅ **Routing logic** for each action  
✅ **Error handling** with helpful error messages  
✅ **Private handler functions** (_handle_*) for each action  
✅ **No import errors** - test imports work  
✅ **Ruff clean** - zero linting errors  
✅ **Type hints** - complete type annotations  

---

## Benefits Summary

### For Users:
- 🎯 Clean, organized tool list (5-10 vs 60+)
- 📚 Easier discovery and learning
- 🔍 Logical grouping by category
- 💡 Better understanding of capabilities
- ⚡ Faster to find what they need

### For Developers:
- 🏗️ Better code organization
- 📦 Modular registration system
- 🔧 Switchable modes (production/testing)
- 🧪 Individual tools still available
- 📖 Self-documenting architecture

### For MCP Clients (Claude):
- 🚀 Discovers all operations at startup
- 📋 Sees enumerated actions in schema
- 💬 Can explain specific capabilities
- ✅ Knows parameter requirements
- 🎨 Better suggestions and routing

---

## Examples from virtualization-mcp

### vm_management Portmanteau:

**Consolidates:**
- list_vms, get_vm_info, create_vm, start_vm, stop_vm, delete_vm, clone_vm, reset_vm, pause_vm, resume_vm

**Into:**
```python
async def vm_management(
    action: Literal["list", "create", "start", "stop", "delete", "clone", "reset", "pause", "resume", "info"],
    vm_name: str | None = None,
    ...
)
```

**Usage:**
```python
# Instead of: await start_vm(vm_name="my-vm")
# Use: await vm_management(action="start", vm_name="my-vm")
```

**User asks:** "Start my VM"  
**Claude uses:** `vm_management(action="start", vm_name="...")`

### Complete Implementation

See: `src/virtualization_mcp/tools/portmanteau/vm_management.py`
- 396 lines
- 10 operations
- Comprehensive docstrings
- Full error handling
- Delegates to individual vm_tools functions
- FastMCP 2.12 compliant

---

## Testing Pattern

### Test Portmanteau Registration:

```python
import pytest
from fastmcp import FastMCP
from virtualization_mcp.tools.portmanteau.vm_management import register_vm_management_tool

def test_vm_management_registration():
    mcp = FastMCP('test')
    register_vm_management_tool(mcp)
    
    # Verify tool registered
    assert 'vm_management' in mcp._tool_manager._tools
    
    # Verify it's callable
    tool = mcp._tool_manager._tools['vm_management']
    assert callable(tool.fn)
    
    # Check signature has Literal
    import inspect
    sig = inspect.signature(tool.fn)
    action_param = sig.parameters['action']
    assert 'Literal' in str(action_param.annotation)
```

### Test Each Operation:

```python
@pytest.mark.asyncio
async def test_vm_management_list():
    from virtualization_mcp.tools.portmanteau.vm_management import register_vm_management_tool
    
    mcp = FastMCP('test')
    register_vm_management_tool(mcp)
    
    # Get the tool function
    tool_fn = mcp._tool_manager._tools['vm_management'].fn
    
    # Test list action
    result = await tool_fn(action="list")
    assert result is not None
    assert "success" in result or "error" in result
```

---

## Summary

### The Portmanteau Pattern Is:

**A design pattern for MCP servers that consolidates many related tools into fewer action-based portmanteau tools, dramatically improving UX while maintaining full functionality.**

### Key Requirements:

1. ✅ Use `Literal` types for action enums (discoverability)
2. ✅ Use `@mcp.tool()` without description (FastMCP 2.12)
3. ✅ Write comprehensive docstrings (document all operations)
4. ✅ Validate imports (no circular dependencies)
5. ✅ Run ruff (code quality)
6. ✅ Test registration (works without errors)
7. ✅ Verify in Claude Desktop (actual usage)

### When to Use:

**Use portmanteau when you have 15+ related tools that conceptually group into 5-10 categories.**

### Example Results:

virtualization-mcp: 60+ tools → 6-7 portmanteau tools (same functionality, 10x cleaner UX)

---

**Status:** Production-ready pattern, proven in virtualization-mcp ✨

