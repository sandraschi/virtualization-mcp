# Tool Registration Refactoring Plan

## Current Issues
1. Mixed tool registration patterns (programmatic + decorators)
2. Inconsistent tool discovery
3. Missing proper docstrings for FastMCP tool discovery

## Phase 1: Preparation (1 day)
1. [ ] Create backup of current state
2. [ ] Document current tool registration patterns
3. [ ] Set up testing environment for tool discovery

## Phase 2: Tool Migration (2 days)
1. [ ] Move tools to their respective modules
   - VM tools → `tools/vm/`
   - Network tools → `tools/network/`
   - Storage tools → `tools/storage/`
   - System tools → `tools/system/`

2. [ ] Update imports in `all_tools_server.py`

## Phase 3: Decorator Implementation (2 days)
1. [ ] Add `@mcp.tool()` decorators to all tool functions
2. [ ] Ensure proper docstring format:
   ```python
   @mcp.tool()
   def tool_name(param: type) -> Dict[str, Any]:
       """
       Tool description
       
       Args:
           param: Parameter description
           
       Returns:
           Dict with status and result/error
       """
   ```

## Phase 4: Testing (1 day)
1. [ ] Verify tool discovery in MCP client
2. [ ] Test all tool functions
3. [ ] Update documentation

## Phase 5: Cleanup (1 day)
1. [ ] Remove old registration code
2. [ ] Update developer documentation
3. [ ] Add tool registration tests

## Risks
1. Tool discovery might break during transition
2. Parameter validation might need updates
3. Documentation might need significant updates
