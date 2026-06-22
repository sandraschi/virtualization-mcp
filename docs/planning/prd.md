# Virtualization MCP - Product Requirements Document (PRD)

## Version: 1.2.1
**Last Updated**: June 2026  
**Status**: Active  
**Author**: Sandra Schipal  
**MCP Version**: 3.4+  
**FastMCP**: >=3.4.2,<4  
**VirtualBox Version**: 7.0+  
**Python**: 3.12+

## 1. Executive Summary

### 1.1 Product Overview
Virtualization MCP (`virtualization-mcp`) is a FastMCP 3.4+ server that provides comprehensive VM management across multiple hypervisors through a unified MCP interface. It manages VirtualBox (local), Hyper-V (local), Windows Sandbox (local), Docker (local containers), and Proxmox VE (remote REST API) — all from the same portmanteau tool surface and web dashboard.

The server ships as a dual-mode application: a stdio MCP server for Claude Desktop/Cursor integration, and a full web dashboard (FastAPI + React + Tauri) for browser-based management and desktop native installation.

### 1.2 Key Benefits
- **Multi-Hypervisor Unified Management**: Manage VirtualBox, Hyper-V, and Proxmox VMs through a single MCP tool surface
- **Windows Sandbox Integration**: Launch disposable Windows environments for fleet install testing, dev setups, and CI-like workflows
- **Desktop Native App**: Tauri 2.0 NSIS installer bundles the Python backend + React frontend into a single Windows `.exe`
- **Natural Language Integration**: Interact with all hypervisors using natural language via Claude Desktop or Cursor
- **Automation Ready**: Portmanteau tools with 60+ operations for programmable VM lifecycle, networking, storage, and snapshots
- **Free and Open**: No license costs — VirtualBox (GPLv2), Hyper-V (Windows built-in), Proxmox (AGPLv3), Docker (Apache 2.0)

## 2. Product Scope

### 2.1 In Scope (v1.0.0 – Core)

#### Hypervisor Support
- **VirtualBox 7+** (primary, local): VM lifecycle, snapshots, networking, storage, VRDP, unattended installs, ISO pipeline
- **Hyper-V** (secondary, Windows): VM lifecycle, Gen2 UEFI support, PowerShell-based management
- **Windows Sandbox** (ephemeral): Consumer, Dev Infra, and Full Dev sandbox modes with automated tooling install
- **Docker** (container): Ephemeral code execution, sandbox-style container management
- **Proxmox VE** (remote, via REST API): VM lifecycle, snapshots, node/cluster status, configured via `PROXMOX_HOST` env var or Settings UI

#### Core Functionality
- **VM Lifecycle Management**: Create, start, stop, pause, resume, reset, delete VMs across all supported hypervisors
- **Snapshot Management**: Create, restore, delete, list snapshots (VirtualBox and Proxmox)
- **Resource Configuration**: CPU, memory, storage, network adapters and modes
- **Template System**: 10+ predefined VM templates (Ubuntu, Windows, Debian, etc.) in `config/vm_templates.yaml`
- **ISO Pipeline**: Download Ubuntu, Debian, Windows ISOs into `assets/vbox` with background thread + progress tracking
- **Unattended Win11 Install**: Auto-generated answer files with optional dev tools

#### MCP Tool Surface
- 8 portmanteau tools with 60+ operations: `vm_management`, `network_management`, `snapshot_management`, `storage_management`, `system_management`, `sandbox_management`, `hyperv_management`, `proxmox_management`
- Agentic tools with `ctx.sample()` support: `suggest_config`, `sandbox_workflow`, `workflow`
- FastMCP 3.4+: Skills provider, prompts, dual transport (stdio + HTTP)

#### Web Dashboard (React + Vite + Tauri)
- 14 pages: Dashboard, VirtualBox, Hyper-V, Proxmox VE, Windows Sandbox, Tools Console, Apps Hub, Prompts & Skills, AI Chat, API Docs, System Logs, Help & Docs, Settings, VM Console
- Dark theme (Zinc-950), glassmorphism, Framer Motion, Recharts, Zustand
- Dynamic tool discovery (no hardcoded tool lists)
- Local LLM auto-discovery (Ollama :11434, LM Studio :1234)
- 6-way provider chat (Ollama, LM Studio, OpenAI, DeepSeek, Anthropic, Gemini)
- Fleet webapp registry and launch

#### Desktop App (Tauri 2.0 + NSIS)
- Single NSIS installer with embedded Python backend (PyInstaller)
- Rust shell spawns backend with `PORT`, `HOST`, `CORS_ORIGINS` env vars
- WebView2 frontend with CORS to `tauri://localhost`
- PREINSTALL/PREUNINSTALL hooks kill both native + backend processes
- Optional MCP client registration in Cursor / Claude Desktop

### 2.2 In Scope (v1.2.x – Current)

- **Proxmox VE REST API client**: Full ticket-based auth, VM lifecycle, snapshots, node/cluster status
- **Settings UI with horizontal tabs**: Local LLM, API Keys, Proxmox VE, Hardware, Alerts
- **Proxmox settings**: Host/user/password/node management via Settings page + backend persistence
- **Proxmox web page**: VM listing filtered from unified `/api/v1/vms` endpoint
- **Horizontal tab help system**: 6 tabs (Getting Started, VirtualBox, Proxmox VE, Windows Sandbox, Desktop App, Troubleshooting, FAQ)
- **Virtualization landscape README**: Full comparison of VirtualBox, Hyper-V, Sandbox, Docker, VMware (Broadcom), Proxmox, KVM, Nutanix AHV, OpenStack, Kubernetes
- **SOTA fixes**: Hardcoded API_BASE, `Stdio::null()` pipe fix, `subprocess.run(timeout=30)` for VBoxManage, removed 10s VM polling, FastAPI 0.138.0 version match, backend-status patience indicator, 90-attempt health check window, restart button bugfix

### 2.3 Future Scope

#### Hypervisor Backends
- **Proxmox VE** (deepen): Snapshot UI in webapp, VM creation dialog, cluster HA status, live migration
- **KVM/libvirt**: Linux-native Type-1 support via `virsh` API
- **VMware**: Only if Broadcom reverses licensing — unlikely; not planned
- **Nutanix AHV**: Enterprise tier — only if a Nutanix cluster is available for testing
- **OpenStack**: Not planned — wrong abstraction layer (multi-tenant cloud vs single-machine VM manager)

#### Desktop App
- **Auto-update**: Tauri updater plugin for in-app update notifications
- **System tray**: Minimize to tray with backend status icon
- **MCP client registration** in NSIS post-install hook (Cursor, Claude Desktop)
- **macOS/Linux builds**: Tauri cross-platform builds (blocked by VirtualBox/Hyper-V Windows dependency)

#### Web Dashboard
- **VM console** via noVNC WebSocket proxy (VRDP bridge)
- **Performance graphs**: CPU/memory/disk time-series across VM lifecycle
- **Batch operations**: Start/stop/snapshot multiple VMs at once
- **Role-based access**: Multi-user auth for team environments

#### MCP Tools
- **Workflow automation**: Composable multi-step VM workflows via `ctx.sample()`
- **Resource optimization**: Suggest VM sizing based on host capacity
- **Backup/restore**: Export/import OVA via MCP tools

## 3. User Stories & Use Cases

### 3.1 Development Workflow
- **Developer Environment**
  - As a developer, I want to quickly spin up pre-configured development environments
  - As a developer, I need to test my code across multiple OS versions
  - As a developer, I want to share my environment configuration with my team

- **Team Collaboration**
  - As a team lead, I want to standardize development environments across the team
  - As a team member, I want to replicate the exact environment my colleague is using
  - As an open-source contributor, I want to provide a consistent environment for testing PRs

### 3.2 Testing & QA
- **Test Automation**
  - As a QA engineer, I want to create disposable test environments
  - As a tester, I need to take snapshots before test runs
  - As a test automation engineer, I want to programmatically control VM states

- **CI/CD Integration**
  - As a devops engineer, I want to automate test environment provisioning
  - As a CI/CD pipeline, I need to spin up clean VMs for each test run
  - As a release manager, I want to verify builds in multiple environments

### 3.3 Education & Training
- **Classroom Environments**
  - As an instructor, I want to distribute pre-configured lab environments
  - As a student, I want to reset my environment to a clean state
  - As a training coordinator, I need to manage multiple student environments

### 3.4 Security Research
- **Malware Analysis**
  - As a security researcher, I need isolated environments for analyzing malware
  - As a pen tester, I want to create attack scenarios in controlled VMs
  - As a security analyst, I need to capture and analyze network traffic from VMs

### 3.5 Enterprise Use Cases
- **Business Continuity**
  - As a system administrator, I need to quickly deploy backup VMs
  - As an IT manager, I want to standardize VM configurations across the organization
  - As a security officer, I need to ensure all VMs meet compliance requirements

## 4. Technical Requirements

### 4.1 System Requirements

#### Host System
- **CPU**: x86_64 with hardware virtualization (Intel VT-x/AMD-V)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 20GB free space minimum (SSD recommended)
- **OS**: 
  - Windows 10/11 64-bit
  - Ubuntu 20.04/22.04 LTS
  - RHEL/CentOS 8/9
  - macOS 12+ (Intel/Apple Silicon)
- **VirtualBox**: 7.0 or later with Extension Pack
- **Python**: 3.8+ with virtualenv

#### Network Requirements
- TCP/IP networking
- Ports: 18083 (MCP server), 3389 (RDP), 22 (SSH)
- Internet access for package installation

### 4.2 Performance Requirements

#### VM Performance
- Startup time: < 10 seconds for minimal VMs
- Snapshot creation: < 30 seconds for typical VMs
- API response time: < 500ms for most operations
- Concurrent VM support: 5+ VMs on recommended hardware

#### Resource Utilization
- Memory overhead: < 100MB per VM
- CPU overhead: < 5% per idle VM
- Storage: Thin provisioning with dynamic allocation

### 4.3 Security Requirements

#### Authentication & Authorization
- API key authentication
- Role-based access control (RBAC)
- Secure credential storage
- Audit logging

#### Isolation
- Network isolation between VMs
- Resource limits and quotas
- Secure snapshot handling
- Anti-malware protection

## 5. MCP Tools Reference

### 5.1 VM Management Tools

#### Core Operations
- `list_vms`: List all available VMs with status
- `create_vm`: Create a new VM with specified parameters
- `start_vm`: Start a stopped VM
- `stop_vm`: Gracefully stop a running VM
- `reset_vm`: Hard reset a VM
- `delete_vm`: Remove a VM and its files

#### Advanced Operations
- `clone_vm`: Create a copy of an existing VM
- `export_vm`: Export VM to OVA/OVF format
- `import_vm`: Import VM from OVA/OVF format
- `register_vm`: Register an existing VM
- `unregister_vm`: Unregister a VM without deleting files

### 5.2 Snapshot Management
- `create_snapshot`: Create a snapshot of a VM
- `restore_snapshot`: Revert VM to a previous snapshot
- `delete_snapshot`: Remove a snapshot
- `list_snapshots`: List all snapshots for a VM
- `get_snapshot_info`: Get detailed info about a snapshot

### 5.3 Network Management
- `list_networks`: List available network interfaces
- `create_nat_network`: Create a new NAT network
- `configure_network_adapter`: Configure VM network settings
- `port_forwarding`: Set up port forwarding rules
- `network_metrics`: Get network performance metrics

### 5.4 Storage Management
- `list_storage_controllers`: List storage controllers
- `attach_disk`: Attach a disk to a VM
- `detach_disk`: Detach a disk from a VM
- `create_disk`: Create a new virtual disk
- `resize_disk`: Resize an existing disk

### 5.5 System & Configuration
- `get_system_info`: Get host system information
- `get_vm_config`: Get VM configuration
- `set_vm_config`: Update VM configuration
- `list_os_types`: List supported guest OS types
- `get_metrics`: Get performance metrics

## 6. API Reference

### 6.1 Authentication
All API requests require an API key in the `X-API-Key` header.

### 6.2 Endpoints

#### VM Management
- `GET /api/v1/vms` - List all VMs
- `POST /api/v1/vms` - Create a new VM
- `GET /api/v1/vms/{vm_id}` - Get VM details
- `PUT /api/v1/vms/{vm_id}` - Update VM configuration
- `DELETE /api/v1/vms/{vm_id}` - Delete a VM
- `POST /api/v1/vms/{vm_id}/start` - Start a VM
- `POST /api/v1/vms/{vm_id}/stop` - Stop a VM
- `POST /api/v1/vms/{vm_id}/reset` - Reset a VM

#### Snapshot Management
- `GET /api/v1/vms/{vm_id}/snapshots` - List snapshots
- `POST /api/v1/vms/{vm_id}/snapshots` - Create snapshot
- `GET /api/v1/vms/{vm_id}/snapshots/{snapshot_id}` - Get snapshot details
- `POST /api/v1/vms/{vm_id}/snapshots/{snapshot_id}/restore` - Restore snapshot
- `DELETE /api/v1/vms/{vm_id}/snapshots/{snapshot_id}` - Delete snapshot

### 6.3 Error Handling
All error responses follow the format:
```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

## 7. Security Considerations

### 7.1 Secure Configuration
- Default to secure settings
- Disable unnecessary services
- Enable encryption where possible
- Regular security updates

### 7.2 Access Control
- Principle of least privilege
- Strong authentication
- Session management
- Audit logging

### 7.3 Data Protection
- Encryption at rest
- Secure credential storage
- Data sanitization
- Secure deletion

## 8. Performance Optimization

### 8.1 Resource Allocation
- CPU pinning
- Memory ballooning
- I/O scheduling
- Network optimization

### 8.2 Storage Optimization
- Disk caching
- Storage controller selection
- Disk image formats
- Compression and deduplication

## 9. Deployment Guide

### 9.1 Installation
```bash
# Install from PyPI
pip install virtualization-mcp

# Or from source
pip install .
```

### 9.2 Configuration
```yaml
# config.yaml
server:
  host: 0.0.0.0
  port: 18083
  debug: false

virtualbox:
  vboxmanage_path: /usr/bin/VBoxManage
  default_folder: ~/VirtualBox VMs

security:
  api_key: your-secure-api-key
  enable_auth: true
  allowed_origins:
    - http://localhost:3000
```

### 9.3 Running the Server
```bash
# Start the MCP server
virtualization-mcp serve --config config.yaml

# Or using Python
python -m virtualization-mcp.server --config config.yaml
```

## 10. Testing Strategy

### 10.1 Unit Tests
- Core functionality
- Error handling
- Edge cases

### 10.2 Integration Tests
- API endpoints
- Tool integration
- End-to-end workflows

### 10.3 Performance Testing
- Load testing
- Stress testing
- Long-running stability

## 11. Maintenance & Support

### 11.1 Versioning
Follows Semantic Versioning (SemVer): MAJOR.MINOR.PATCH

### 11.2 Upgrade Path
- Backward compatibility maintained within major versions
- Upgrade guides for major version changes
- Deprecation notices in advance

### 11.3 Support
- Documentation
- Community forum
- Issue tracker
- Commercial support options

## 12. Roadmap

### 12.1 v1.1.0 (Q4 2025)
- Enhanced storage management
- Improved network topologies
- Advanced monitoring

### 12.2 v1.2.0 (Q1 2026) ✅
- FastMCP 3.1 prompts and skills
- Webapp Prompts & Skills page, health wait, status API

### 12.3 v1.3.0 (Q2 2026) ✅
- Windows Sandbox dev setup (automated winget + optional tools selection)
- Assets folders (sandbox, vbox) and webapp integration
- AIRGAP and host Ollama options for Sandbox
- Create VM / Attach ISO from assets/vbox; Win 11 Pro template and OVA asset workflow
- Interactive System Logs and Help Terminal UI in the webapp dashboard
- 6-way LLM integration with local settings persistence and port self-healing
- Hyper-V Gen2 VM creation UEFI boot order resolution fixes

### 12.4 v2.0.0 (Q3 2026)
- Multi-hypervisor support
- Web-based management UI
- Plugin system

## 13. Appendix

### 13.1 Troubleshooting
Common issues and solutions

### 13.2 FAQ
Frequently asked questions

### 13.3 Glossary
Terminology and concepts

### 13.4 References
- VirtualBox Documentation
- MCP Specification
- Security Best Practices

### 4.1 Core Functionality
- MCP 2.10+ Protocol Compliance
- VirtualBox 7.0+ Integration
- Async I/O Operations
- Comprehensive Error Handling
- Logging and Diagnostics

### 4.2 Performance
- Sub-second response time for basic operations
- Support for 50+ concurrent VM operations
- Efficient resource utilization
- Minimal memory footprint

### 4.3 Security
- Secure command execution
- Input validation and sanitization
- Principle of least privilege
- Secure credential management

## 5. User Interface

### 5.1 MCP Interface
- Standard MCP tool registration
- Self-documenting API
- Consistent response formats
- Error codes and messages

### 5.2 Logging
- Structured logging (JSON)
- Multiple log levels
- Rotating log files
- Sensitive data redaction

## 6. Integration Points

### 6.1 VirtualBox
- VBoxManage CLI integration
- VirtualBox Web Services API
- VirtualBox SDK (future)

### 6.2 MCP Ecosystem
- Claude Desktop
- Windsurf Next
- Other MCP 2.10+ clients

## 7. Non-Functional Requirements

### 7.1 Reliability
- 99.9% uptime for MCP server
- Graceful error recovery
- Transactional operations where possible

### 7.2 Performance
- <100ms response time for status queries
- <1s for VM state changes
- Efficient memory usage

### 7.3 Security
- No storage of sensitive data
- Input validation
- Secure process execution

## 8. Success Metrics

### 8.1 KPIs
- Number of successful VM operations
- Average operation latency
- Error rates
- User adoption rate

### 8.2 Monitoring
- Performance metrics collection
- Error tracking
- Usage statistics

## 9. Dependencies
- Python 3.8+
- VirtualBox 7.0+
- FastMCP 2.10+

## 10. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| VirtualBox API changes | High | Medium | Version pinning, CI testing |
| Security vulnerabilities | Critical | Low | Regular updates, security audits |
| Performance issues | Medium | Medium | Profiling, optimization |
| Compatibility issues | High | Low | Comprehensive testing |

## 11. Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| v1.0.0 Release | 2025-08-10 | ✅ Complete |
| v1.0.1b2 Quality Pass | 2025-10-20 | ✅ Complete |
| v1.1.0 Multi-Provider | 2026-03-03 | ✅ Complete |
| v1.2.0 FastMCP 3.1 & webapp | 2026-03-05 | ✅ Complete |
| v1.3.0 Sandbox full dev, logs, 6-way LLMs & assets | 2026-06 | ✅ Complete |
| v1.4.0 Cloud integration | 2026-Q3 | 📅 Planned |

## 12. Approval

| Role | Name | Approval Date |
|------|------|---------------|
| Product Owner | | |
| Engineering Lead | | |
| QA Lead | | |

---
*Document Version: 1.0.0*  
*Last Updated: 2025-08-10*



