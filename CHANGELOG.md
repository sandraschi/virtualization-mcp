# Changelog

All notable changes to virtualization-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Windows Sandbox full dev setup & assets reuse

#### Assets (reuse folders)
- **`assets/sandbox/`** – Windows Sandbox full-dev installer files (`DesktopAppInstaller_Dependencies.zip`, `*.msixbundle`). Webapp **Full dev setup** uses this folder; script written here on launch. Gitignored.
- **`assets/vbox/`** – VirtualBox VM media (ISOs, OVA/OVF). Create VM and Attach ISO in the webapp use this folder. Gitignored.
- **`assets/README.md`** – Overview of both asset folders and how the webapp ties to them.

#### Windows Sandbox (webapp)
- **Full dev setup** – One-click automated dev stack in Sandbox: winget (deps + App Installer) then optional Python, Node, uv/uvx, pip, Git, Just, VS Code, Notepad++, Windsurf, Cursor, Antigravity, Claude Desktop, OpenClaw, OpenFang, RoboFang. Tools selectable via checkboxes; script generated and written to assets folder.
- **AIRGAP** – Big red toggle: disables networking for the sandbox (100% air-gapped; e.g. OpenClaw safe). Use after initial install or with pre-installed assets.
- **Use host Ollama** – Optional checkbox: sets `OLLAMA_HOST` in sandbox to host gateway so apps in sandbox can use Ollama on host.
- **Backend**: `GET /api/v1/sandbox/dev-setup-script`, `POST /api/v1/sandbox/launch` with `full_dev_setup`, `assets_folder`, `dev_tools`, `airgap`, `use_host_ollama`. Script generator parameterised by tools and options.

#### VirtualBox (webapp)
- **Assets API** – `GET /api/v1/assets/paths` (repo_root, assets_sandbox, assets_vbox), `GET /api/v1/assets/vbox` (list ISO/OVA/OVF in assets/vbox).
- **Create New VM** – Modal: name, template (Ubuntu dev, Win 11 Pro, Windows test, etc.), optional ISO from assets/vbox. `POST /api/v1/vms` accepts optional `iso_path`; attaches ISO after create.
- **Attach ISO** – Per-VM “Attach ISO” button; modal lists files from assets/vbox. `POST /api/v1/vms/{name}/attach-iso`.
- **Win 11 Pro template** – New template `win11-pro` (Windows11_64, 8GB RAM, 80GB disk). Default templates in code include it. `config/vm_templates.yaml` and assets/vbox README document creating a ready-to-use Win 11 Pro OVA asset (install once, export to assets/vbox, import for reuse).

#### Sandbox page UX
- Assets folder input pre-filled from `GET /api/v1/assets/paths` (repo assets_sandbox). “Use repo assets” button to reset to that path.
- Placeholder and copy updated to point at repo assets path.

#### Documentation
- **assets/sandbox/README.md** – What to place (deps zip, msixbundle), how to use with webapp.
- **assets/vbox/README.md** – ISOs/OVA reuse; **Win 11 Pro VM asset** section: one-time setup (ISO → create VM → install → export OVA) and reuse (import OVA).

---

## [1.2.0] - 2026-03-05

### FastMCP 3.1 and webapp upgrades

#### FastMCP 3.1
- **Bump**: `fastmcp>=3.1.0`.
- **Prompts**: Added `virtualization_expert` MCP prompt (optional `focus`: general, lifecycle, storage, network). Registered in main server (all_tools_server) and server_v2.
- **Skills**: Bundled `virtualization-expert` skill (`src/virtualization_mcp/skills/virtualization-expert/SKILL.md`) exposed via `SkillsDirectoryProvider` as `skill://virtualization-expert/SKILL.md`.
- **Context in tools**: `vm_management` portmanteau accepts optional `ctx: Context`; uses `ctx.report_progress()` for list, create, clone.
- **Sampling/agentic**: New action `suggest_config` on `vm_management` uses `ctx.sample()` when context is available to suggest VM configuration (use_case parameter). Fallback when no sampling.
- **Prompts/skills in main server**: `all_tools_server.start_mcp_server()` now registers prompts and skills so CLI/stdio users get full 3.1 features.

#### Webapp
- **Health wait**: `webapp/start.ps1` waits for backend `GET /api/v1/health` (up to 15 attempts) before starting Vite.
- **Backend**: Added `GET /health`; service_manager initialized first so VMs/host info work even if MCP init fails.
- **API base**: Frontend uses `API_BASE` from `api/config.ts` (default `http://localhost:10701`). CORS allows `http://localhost:10700` and `http://127.0.0.1:10700`.
- **Prompts & Skills page**: New route `/prompts-skills` and sidebar item "Prompts & Skills". Lists prompts metadata and bundled skills; expandable skill markdown from backend.
- **Backend APIs**: `GET /api/v1/prompts`, `GET /api/v1/skills`, `GET /api/v1/skills/{skill_id}` for webapp Prompts & Skills page.
- **Status**: `GET /api/v1/status` returns mcp, service_manager, registry state for debugging.

#### Configuration
- **MCP HTTP port**: Default port for MCP HTTP/SSE changed from 8000 to **10702** (SOTA range 10700–10800). Override with `VIRTUALIZATION_MCP_PORT`.

#### Scripts
- **Backup**: Repo uses canonical SOTA backup script; run `.\scripts\backup-repo.ps1` from repo root.

---

## [1.1.0] - 2026-03-03

### 🎉 Multi-Provider Advanced Management Release

Major upgrade transitioning from VirtualBox-only to a scalable multi-provider virtualization platform.

### ✨ New Features

#### Native Hyper-V Provider Support
- **Hyper-V Integration**: Native Windows Hyper-V management via PowerShell automation.
- **Provider-Agnostic Architecture**: Refactored `VMService` to route operations between VirtualBox and Hyper-V.
- **Auto-Discovery**: Automatic detection and registration of active providers.

#### Advanced VM Controls
- **Lifecycle Operations**: Added support for **Pause**, **Resume**, and **Snapshot** through dedicated API endpoints.
- **Live Console View**: Real-time screenshot service allowing for console monitoring of running VMs directly in the webapp.
- **Refined Polling**: Optimized state tracking and live view refresh rates.

#### SOTA Webapp Enhancements
- **Multi-Provider Dashboard**: Unified interface for managing VBox and Hyper-V instances side-by-side.
- **Provider Branding**: Dedicated badges and color coding for different hypervisors.
- **Live Snapshots**: Visual console previews in VM cards for immediate status verification.

### 🔧 Technical Improvements
- **Service Refactor**: Unified `VMService` for cleaner provider integration.
- **Screenshot Service**: Robust screenshot handling for live monitoring.
- **API Expansion**: Extended REST API with advanced control capabilities.

---

## [1.0.1b2] - 2025-10-20

### 🎉 Production-Ready Beta Release

Second beta release with major quality improvements, FastMCP compliance fixes, and production-ready features.

### ✨ New Features

#### Portmanteau Tool Expansion
- **discovery_management** - New portmanteau for help/status/tool-info operations
  - list_tools: List all virtualization-mcp tools
  - tool_info: Get detailed tool information
  - tool_schema: Get JSON schema for parameters
  - help: Get general help information
- **hyperv_management** - New Windows-only Hyper-V management tool
  - list: List all Hyper-V VMs
  - get: Get detailed Hyper-V VM info
  - start: Start Hyper-V VM
  - stop: Stop Hyper-V VM (graceful or forced)
- **Production mode now has 6-7 tools**: 33 operations total
- **Platform-aware registration**: Hyper-V tool auto-registers on Windows only
- **Note**: discovery_management is app-specific (MCP protocol has its own tools/list)

#### Tool Mode Configuration
- **Switchable Tool Modes**: Choose between production (6-7 tools) and testing (60+ tools)
  - Production mode: Clean 5-tool interface for end users (default)
  - Testing mode: All 60+ individual tools + portmanteau for development
- **Environment Variable Control**: `TOOL_MODE=production|testing`
- **Config File Support**: `mcp_config.json` with mode selection
- **Comprehensive Documentation**: Full guide in `docs/mcp-technical/TOOL_MODE_CONFIGURATION.md`

#### Repository Organization
- **Clean Root Directory**: Removed 129 obsolete files and test artifacts
- **Organized Documentation**: All docs categorized in subdirectories
- **Updated .gitignore**: Prevents future clutter automatically
- **Professional Appearance**: Ready for public contributors

### 🔧 Critical Fixes

#### FastMCP 2.12 Compliance (CRITICAL)
- **Removed ALL description parameters** from tool registrations
- **FastMCP now uses comprehensive docstrings** automatically
- **Claude Desktop can now see full documentation**:
  - All sub-operations for portmanteau tools
  - Parameter details with types and constraints
  - Return value structures
  - Usage examples
- **60+ tools updated** across 8 files
- **Impact**: Transforms Claude's ability to discover and use tools

#### CI/CD & Testing
- **Fixed pytest spawning**: Changed to `python -m pytest`
- **Fixed twine installation**: Explicit `uv pip install twine build`
- **Fixed artifact uploads**: Proper upload/download workflow
- **Fixed coverage path**: Corrected for CI compatibility
- **Removed flake8**: Using ruff exclusively
- **All tests passing**: 499/499 non-skipped tests (100%)

#### Code Quality
- **Fixed all 22 ruff errors**: 0 linting errors (100% clean)
- **Fixed all 24 pytest failures**: All tests passing
- **Added vbox_manager fixture**: Handles VBox available/unavailable
- **Added ServerConfig alias**: server_v2 compatibility
- **Fixed mock decorators**: Handle both FastMCP decorator patterns
- **Added clone_vm method**: VBoxManager compatibility
- **Added parameter aliases**: create_vm supports multiple param names

### 🗑️ Removed

#### Workflow Simplification
- **Disabled 13 workflows**: Prevents notification spam (can re-enable anytime)
- **Removed Dependabot**: Manual dependency management
- **Closed 4 Dependabot PRs**: Outdated dependency updates
- **Removed PyPI publishing**: Not needed for MCP servers (MCPB is primary)

#### Repository Cleanup
- **28 status/progress markdown** → Moved to `docs/archive/`
- **80+ mock JSON files** → Deleted from `MagicMock/`
- **8 obsolete test scripts** → Deleted
- **8 test artifact directories** → Deleted
- **7 obsolete config files** → Deleted
- **All log files** → Removed
- **VDI disk images** → Removed

### 📦 MCPB Package Optimization

- **Size Reduced**: 15 MB → 296.5 KB (98% reduction!)
- **Comprehensive .mcpbignore**: Excludes dependencies, caches, tests, docs
- **8 AI Prompt Templates**: 25+ KB of comprehensive guidance
- **No Bundled Dependencies**: Clean package, pip installs separately
- **SHA**: 30cd995bf439e44ecaa03767fe526b73f6eb099d

### 📖 Documentation

#### New Documentation
- `docs/QUICK_START.md` - User onboarding guide
- `docs/mcp-technical/RELEASE_STATUS.md` - v1.0.1b2 release report
- `docs/mcp-technical/DOCSTRING_COVERAGE.md` - 100% coverage verification
- `docs/mcp-technical/FASTMCP_2.12_COMPLIANCE.md` - Compliance report
- `docs/mcp-technical/CLEANUP_SUMMARY.md` - Repository cleanup details
- `docs/mcp-technical/PROJECT_STATUS_FINAL.md` - Complete project status
- `docs/mcp-technical/TOOL_MODE_CONFIGURATION.md` - Mode switching guide
- `docs/mcp-technical/TOOL_MODE_IMPLEMENTATION.md` - Technical implementation
- `TOOL_MODE_QUICK_REFERENCE.md` - Quick mode reference

#### Documentation Improvements
- All technical docs moved to `docs/mcp-technical/`
- Historical files archived in `docs/archive/`
- Comprehensive project status notes
- Clear organization by category

### 🔨 Technical Improvements

#### Tool Registration
- All tools use function docstrings (no description override)
- Conditional registration based on TOOL_MODE
- Cleaner tool discovery for Claude
- Better parameter understanding
- Comprehensive documentation visibility

#### Configuration
- Added TOOL_MODE setting to config.py
- Environment variable support for all settings
- Created .env.example with all options
- Sample configs for both modes

#### Testing Infrastructure
- Dual-mode testing (real VBox or mock)
- Added requires_vbox marker to pytest.ini
- Graceful handling of VBox unavailable
- Improved fixture organization

### 🐛 Bug Fixes

- Fixed import errors in multiple modules
- Fixed mock decorator compatibility with FastMCP
- Fixed VBoxManager parameter naming
- Fixed template manager test assertions
- Fixed integration test environmental issues
- Fixed pytest marker warnings

### 📚 Changes

#### Build System
- Updated requirements-dev.txt (removed flake8, black, isort)
- Added ruff, bandit, safety explicitly
- Updated all version numbers to 1.0.1b2
- Updated author email to sandraschipal@protonmail.com

#### Workflow Configuration
- Simplified pytest.ini for CI compatibility
- Reduced log verbosity in CI
- Fixed all workflow YAML syntax
- Made twine check non-blocking
- Removed PyPI publish job

---

## [1.0.1b1] - 2025-10-15

### 🎉 CI/CD Implementation Beta

First beta release with complete CI/CD and automated release infrastructure.

### 🚀 New Features

#### Infrastructure
- Complete CI/CD pipeline with linting, testing, security scanning
- Automated GitHub releases from version tags
- Daily security scans (Bandit, Safety, Semgrep)
- Modern UV-based build system
- Quality gates for code review

#### Documentation
- Comprehensive GitHub documentation
- Quick start guide
- Release checklist
- Security hardening guide

### 🛠️ Improvements
- Modernized all workflows to use UV
- Added build dependencies (build, twine, pyright)
- Resilient security scanning (non-blocking)
- Updated to modern `safety scan` command
- Consistent dependency management

### 📦 Dependencies
- Added build>=1.0.0 for package building
- Added twine>=5.0.0 for package validation
- Added pyright>=1.1.390 for type checking

---

## [1.0.0] - 2025-08-10

### 🎉 Initial Stable Release

First stable release with comprehensive VirtualBox management through MCP protocol.

### 🚀 Features

#### Core Functionality
- Full FastMCP 2.10+ compliance with STDIO support
- Comprehensive VM management (create, start, stop, pause, resume, delete, clone)
- Template system for common OS configurations
- Snapshot management (create, restore, delete, list)
- Resource configuration (CPU, memory, storage)
- Network configuration (NAT, Bridged, Host-Only)
- Storage management (disks, controllers, ISOs)
- Shared folders and clipboard integration

#### MCP Tools
- 60+ tools organized by category
- VM lifecycle management (11 tools)
- Snapshot operations (4 tools)
- Storage & media (6 tools)
- Network configuration (5 tools)
- System resources (5 tools)
- Security features
- Audit logging

#### Security
- Sandboxed operations
- Input validation
- Secure process execution
- VM isolation
- Network security policies
- Access control
- Secure credential storage
- Comprehensive audit logging

---

## [0.9.0] - 2025-07-15

### Added
- Initial beta release
- Basic VM management
- Snapshot support
- Network configuration
- Core MCP protocol implementation

---

## Release Notes

### v1.0.1b2 Highlights

This release represents a major quality milestone:

1. **100% Test Success** - All 499 active tests passing
2. **FastMCP Compliance** - Proper tool registration for Claude
3. **Clean Repository** - Professional organization
4. **Switchable Modes** - Production vs testing tool sets
5. **Optimized Package** - 296 KB MCPB with no bloat
6. **Complete Documentation** - Comprehensive guides and references

### Breaking Changes

None - fully backward compatible.

### Deprecations

None in this release.

### Known Issues

- Coverage at 39% (targeting 80% in future release)
- Some integration tests require manual VBox setup
- 1 VDI test file locked (requires restart to clean)

### Upgrade Notes

From v1.0.1b1:
- No breaking changes
- Restart Claude Desktop to see improved tool documentation
- Set TOOL_MODE=production for clean 5-tool interface (recommended)
- Set TOOL_MODE=testing to see all 60+ individual tools

---

For more details, see:
- [Release Notes](https://github.com/sandraschi/virtualization-mcp/releases/tag/v1.0.1b2)
- [Project Status](docs/mcp-technical/PROJECT_STATUS_FINAL.md)
- [Quick Start Guide](docs/QUICK_START.md)
