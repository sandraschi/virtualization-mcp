# Virtualization-MCP MCPB Package

This directory contains all files needed to build the MCPB (MCP Bundle) package for Claude Desktop installation.

## Directory Structure

```
mcpb/
├── manifest.json              # Runtime configuration for Claude Desktop
├── README.md                  # This file
├── prompts/                   # Extensive prompt templates
│   ├── system.md             # System prompt (AI role and capabilities)
│   ├── user.md               # User prompt template (operation examples)
│   ├── examples.json         # Example interactions
│   ├── vm-creation-wizard.md # VM creation guidance
│   ├── snapshot-strategy.md  # Snapshot best practices
│   ├── network-configuration.md # Network setup guidance
│   ├── troubleshooting-guide.md # Systematic troubleshooting
│   └── advanced-workflows.md # Complex multi-VM workflows
└── assets/                    # Package assets
    ├── icon.png              # Extension icon
    └── screenshots/          # Screenshots for store listing
```

## Prompt Templates

The prompts directory contains comprehensive guidance for the AI assistant:

### Core Prompts (Required by MCPB)
- **system.md**: Defines AI capabilities, tool usage guidelines, and response formats
- **user.md**: Template for common user operations and workflows
- **examples.json**: Example interactions showing expected behavior

### Specialized Templates (Advanced Guidance)
- **vm-creation-wizard.md**: Step-by-step VM creation for different use cases
- **snapshot-strategy.md**: Best practices for snapshot management and cleanup
- **network-configuration.md**: Complete network setup guide for all scenarios
- **troubleshooting-guide.md**: Systematic approach to diagnosing and fixing issues
- **advanced-workflows.md**: Multi-VM deployments and complex scenarios

## Building the Package

### Local Build

```powershell
# From project root
cd mcpb
mcpb pack . ../dist/virtualization-mcp-v1.0.1b1.mcpb
```

### Using Build Script

```powershell
# From project root
.\scripts\build-mcpb-package.ps1 -NoSign
```

### GitHub Actions (Automated)

Push a version tag to trigger automatic building:

```bash
git tag -a v1.0.1b1 -m "Beta release"
git push origin v1.0.1b1
```

## Installation

1. Download the `.mcpb` file from GitHub releases
2. Drag and drop it into Claude Desktop
3. Configure VirtualBox paths when prompted
4. Restart Claude Desktop
5. The virtualization-mcp server will be available

## User Configuration

When installed, users are prompted for:

1. **VirtualBox Installation Directory**
   - Default: `C:\Program Files\Oracle\VirtualBox`
   - Auto-detected if VBoxManage is in PATH

2. **VirtualBox User Home**
   - Default: `${HOME}\VirtualBox VMs`
   - Where VMs and settings are stored

3. **Debug Mode** (Optional)
   - Default: `false`
   - Enable for detailed logging

## Package Contents

- **Source Code**: Complete Python package
- **Dependencies**: FastMCP 2.12.2+ and all requirements
- **Prompts**: 5 comprehensive prompt templates
- **Metadata**: Icons, screenshots, documentation
- **Configuration**: manifest.json and all settings

## Tools Included

- 50+ VM management tools across 8 categories
- Portmanteau tools for complex workflows
- Hyper-V integration (Windows)
- Security and malware analysis
- Monitoring and metrics
- Backup and recovery

See `manifest.json` for complete tool list.

## Documentation

For complete MCPB packaging documentation, see:
- `/docs/mcpb-packaging/MCPB_BUILDING_GUIDE.md` - Comprehensive building guide
- `/docs/mcpb-packaging/MCPB_IMPLEMENTATION_SUMMARY.md` - Implementation status
- `/docs/mcpb-packaging/README.md` - Documentation index

## Version

Current version: **1.0.1b1** (Beta)

Synchronized with:
- `pyproject.toml`
- `src/virtualization_mcp/__init__.py`
- `mcpb/manifest.json`
- Root `mcpb.json`

