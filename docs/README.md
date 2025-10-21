# Public Documentation

**Professional documentation for virtualization-mcp**

This directory contains polished, user-facing documentation that is published on GitHub.

---

## 📚 Documentation Structure

### [`mcpb-packaging/`](mcpb-packaging/)
**MCPB package creation and distribution**
- Complete packaging guide
- Building .mcpb files
- Claude Desktop integration
- Release workflow

### [`portmanteau-pattern/`](portmanteau-pattern/)
**Universal pattern for MCP servers with many tools**
- Complete concept guide (600+ lines)
- FastMCP 2.12 best practices
- Discoverability patterns
- Implementation examples
- Reusable for any MCP server

### [`mcp-technical/`](mcp-technical/)
**Technical implementation details**
- Tool mode configuration
- FastMCP compliance
- Production checklist
- Technical patterns

### [`github/`](github/)
**CI/CD and automation**
- GitHub Actions setup
- Workflow configuration
- Automated testing
- Release automation

---

## 📋 Documentation Standards

### ✅ All Public Docs Should:

1. **Be Professional**
   - Polished writing
   - Complete examples
   - No rough drafts

2. **Be Useful**
   - Solve real problems
   - Provide clear guidance
   - Include working examples

3. **Be Maintained**
   - Keep up-to-date
   - Remove obsolete content
   - Version appropriately

4. **Be Universal**
   - Applicable beyond this repo
   - Teach patterns, not just specifics
   - Help the community

### ❌ Keep Out of Public Docs:

- Progress reports (use docs-private/)
- Debug notes (use docs-private/)
- Personal todos (use docs-private/)
- "Blooper" logs (use docs-private/)
- Scratch notes (use docs-private/)
- WIP documentation (finish first!)

---

## 🎯 Target Audiences

### Users
- How to install and use
- What problems it solves
- Integration guides
- Quick starts

### Developers
- Architecture and patterns
- How to contribute
- Technical reference
- Testing guidelines

### Community
- Reusable patterns
- Lessons learned
- Best practices
- Standards

---

## 📝 Contributing to Docs

When adding new documentation:

1. **Choose the right location:**
   - User guides → Root or specific feature folder
   - Patterns → `portmanteau-pattern/` or similar
   - Technical details → `mcp-technical/`
   - Internal notes → `docs-private/` (git-ignored)

2. **Follow standards:**
   - Clear headings
   - Working examples
   - Table of contents for long docs
   - Links to related docs

3. **Keep it current:**
   - Update when code changes
   - Remove obsolete sections
   - Version appropriately

4. **Review before commit:**
   - Spell check
   - Test all examples
   - Verify links work

---

**Remember:** If it's rough, incomplete, or just for you → `docs-private/`  
**If it's polished and helps others → `docs/`** ✨
