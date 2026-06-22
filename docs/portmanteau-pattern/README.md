# Portmanteau Pattern Documentation

**Location:** `docs/portmanteau-pattern/`  
**Purpose:** Complete guide to the portmanteau tool consolidation pattern for MCP servers

---

## 📚 Documentation Files

### [PORTMANTEAU_CONCEPT.md](PORTMANTEAU_CONCEPT.md)
**Complete 600+ line guide covering:**
- The tool explosion problem
- Portmanteau solution explained
- Universal applicability (any MCP server with 15+ tools)
- virtualization-mcp as reference implementation
- FastMCP 2.12 compliance requirements
- 7 common traps and pitfalls
- Step-by-step implementation guide
- Quality checklist
- Maintenance guidelines
- Real-world examples (AWS, Git, Kubernetes)

**Read this first** if you're implementing portmanteau pattern in your MCP server.

### [MCP_PORTMANTEAU_BEST_PRACTICES.md](MCP_PORTMANTEAU_BEST_PRACTICES.md)
**Critical pattern for discoverability:**
- Why `Literal` types are REQUIRED for action parameters
- How FastMCP generates JSON schemas from type hints
- What MCP clients see at startup
- Complete implementation examples
- Testing discoverability

**Key insight:** `Literal["op1", "op2"]` → Schema enum → Claude discovers all operations!

### [WHAT_CLAUDE_SEES.md](WHAT_CLAUDE_SEES.md)
**Proof of discoverability:**
- What Claude Desktop sees when you ask "list virtualization tools"
- How Literal types create schema enums
- Complete sub-operation discovery at startup
- No extra search steps needed

**Shows the actual user experience** with portmanteau tools.

### [TOOL_MODE_QUICK_REFERENCE.md](TOOL_MODE_QUICK_REFERENCE.md)
**Quick guide to production vs testing modes:**
- Production: 6-7 portmanteau tools (clean UX)
- Testing: 60+ individual tools (development)
- How to switch between modes
- Configuration examples

**For end users and developers** who need to switch modes.

---

## 🎯 When to Read Each Doc

### Building an MCP Server?
**Start with:** [PORTMANTEAU_CONCEPT.md](PORTMANTEAU_CONCEPT.md)
- Understand the pattern
- See if it applies to your server (15+ related tools)
- Follow implementation guide
- Use quality checklist

### Adding Portmanteau to Existing Server?
**Read:**
1. [PORTMANTEAU_CONCEPT.md](PORTMANTEAU_CONCEPT.md) - Implementation guide
2. [MCP_PORTMANTEAU_BEST_PRACTICES.md](MCP_PORTMANTEAU_BEST_PRACTICES.md) - Literal types pattern
3. Check virtualization-mcp source code (reference implementation)

### Debugging Discoverability Issues?
**Check:** [MCP_PORTMANTEAU_BEST_PRACTICES.md](MCP_PORTMANTEAU_BEST_PRACTICES.md)
- Forgot Literal type?
- Used description parameter?
- Incomplete docstring?

### Explaining to Users?
**Share:** [WHAT_CLAUDE_SEES.md](WHAT_CLAUDE_SEES.md)
- Shows actual discovery experience
- Proves pattern works
- Demonstrates UX benefits

---

## 💡 Key Concepts

### The Problem
**MCP servers with 50-100+ individual tools:**
- Overwhelming for users
- Difficult to discover related operations
- Poor UX in Claude Desktop
- Hard to maintain consistency

### The Solution
**Portmanteau tools (action-based consolidation):**
- 60 tools → 6 portmanteau tools
- Same functionality, 10x cleaner UX
- Perfect discoverability via Literal types
- Logical grouping by category

### Critical Requirements (FastMCP 2.12)
1. ✅ Use `Literal` types for action parameters (schema enums)
2. ✅ Use `@mcp.tool()` without description (uses docstring)
3. ✅ Write comprehensive docstrings (document all operations)

### Results
**virtualization-mcp:** 60+ tools → 6-7 portmanteau tools (production-ready)

---

## 🔗 Related Documentation

- `src/virtualization_mcp/tools/portmanteau/` - Source code (reference implementation)
- `docs/mcp-technical/TOOL_MODE_CONFIGURATION.md` - Tool mode system details
- `docs/mcp-technical/MCP_PRODUCTION_CHECKLIST.md` - Production readiness

---

## 🏷️ Tags

`portmanteau-pattern` `tool-consolidation` `fastmcp-2.12` `mcp-protocol` 
`design-pattern` `universal-pattern` `best-practices` `discoverability`

---

**Status:** Complete pattern documentation, production-proven ✨

