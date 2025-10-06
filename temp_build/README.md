# VirtualBox MCP Server

**FastMCP 2.0 server for comprehensive VirtualBox management through Claude Desktop**

[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.1-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![VirtualBox](https://img.shields.io/badge/VirtualBox-7.0+-orange)](https://virtualbox.org)

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repository-url> virtualization-mcp
cd virtualization-mcp
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your VirtualBox paths

# 3. Test the server
fastmcp dev server.py
# Opens MCP Inspector at http://127.0.0.1:6274

# 4. Try it out
"Create an Ubuntu development VM with 4GB RAM"
"Take a snapshot called 'clean-state' of my test VM"
"Set up a multi-VM environment for load testing"
```

## ⚡ Features

### **Complete VM Lifecycle Management**

- Create VMs from 10+ pre-built templates
- Start, stop, pause, and delete VMs
- Template-based rapid deployment
- Resource configuration (memory, disk, network)

### **Professional Testing Workflows**

- Snapshot-based testing with rollback
- Multi-VM environment automation
- Linked VM cloning for efficiency
- Automated testing environment setup

### **Network & File Operations**

- Port forwarding configuration
- File transfer between host and VMs
- Command execution in VMs
- Network connectivity testing

### **Austrian Efficiency Design**

- Minutes to deployment, not hours
- Template-driven VM creation
- Comprehensive error handling
- Direct, actionable responses

## 🛠 MCP Tools Reference

### VM Lifecycle

| Tool | Description | Example |
|------|-------------|---------|
| `create_vm` | Create VM from template | `create_vm("dev-vm", "ubuntu-dev", memory_mb=4096)` |
| `start_vm` | Start virtual machine | `start_vm("dev-vm", headless=True)` |
| `stop_vm` | Stop VM gracefully | `stop_vm("dev-vm")` |
| `delete_vm` | Delete VM and disk | `delete_vm("dev-vm", delete_disk=True)` |
| `list_vms` | List all VMs by state | `list_vms("running")` |

### Snapshot Management

| Tool | Description | Example |
|------|-------------|---------|
| `create_snapshot` | Create testing snapshot | `create_snapshot("test-vm", "before-deploy")` |
| `restore_snapshot` | Rollback to snapshot | `restore_snapshot("test-vm", "clean-state")` |
| `delete_snapshot` | Remove snapshot | `delete_snapshot("test-vm", "old-snapshot")` |
| `list_snapshots` | Show all snapshots | `list_snapshots("test-vm")` |

### Testing Workflows

| Tool | Description | Example |
|------|-------------|---------|
| `clone_vm` | Clone VM for testing | `clone_vm("template", "test-1", linked=True)` |
| `rollback_and_restart` | Atomic rollback+restart | `rollback_and_restart("test-vm", "clean")` |
| `setup_test_environment` | Multi-VM environment | `setup_test_environment("load-test", vm_specs)` |

### Network & System

| Tool | Description | Example |
|------|-------------|---------|
| `configure_port_forwarding` | Setup port forwarding | `configure_port_forwarding("web-vm", 8080, 80)` |
| `get_vm_info` | VM status and config | `get_vm_info("dev-vm")` |
| `get_vm_metrics` | Resource usage | `get_vm_metrics("test-vm")` |
| `execute_command` | Run command in VM | `execute_command("vm", "systemctl status")` |

## 📋 VM Templates

### Available Templates

| Template | OS | Memory | Disk | Use Case |
|----------|----|---------|----- |----------|
| `ubuntu-dev` | Ubuntu 22.04 | 4GB | 25GB | Development with Docker, Git, Node.js |
| `windows-test` | Windows 11 | 8GB | 60GB | Windows application testing |
| `minimal-linux` | Ubuntu | 1GB | 10GB | Quick tests, CI/CD runners |
| `database-server` | Ubuntu | 6GB | 40GB | PostgreSQL, MySQL development |
| `web-server` | Ubuntu | 2GB | 20GB | Nginx, Apache testing |
| `docker-host` | Ubuntu | 4GB | 30GB | Docker container development |
| `security-test` | Kali Linux | 4GB | 25GB | Security testing, penetration |
| `kubernetes-node` | Ubuntu | 6GB | 35GB | K8s cluster nodes |
| `monitoring-stack` | Ubuntu | 4GB | 30GB | Prometheus, Grafana setup |
| `jenkins-ci` | Ubuntu | 4GB | 30GB | Jenkins CI/CD server |

### Custom Templates

```yaml
# config/vm_templates.yaml
custom-template:
  os_type: "Ubuntu_64"
  memory_mb: 2048
  disk_gb: 20
  network: "NAT"
  description: "Custom development setup"
  post_install:
    - docker
    - nodejs
    - postgresql
```

## 💬 Usage Examples

### Development Workflow

```
Claude: "I need a clean Ubuntu development environment"
You: create_vm("dev-clean", "ubuntu-dev")

Claude: "Take a snapshot before I install experimental packages"
You: create_snapshot("dev-clean", "pre-experiment", "Before experimental setup")

Claude: "Something broke, rollback and restart the VM"
You: rollback_and_restart("dev-clean", "pre-experiment")
```

### Testing Environment

```
Claude: "Set up load testing with 3 web servers"
You: setup_test_environment("load-test", [
  {"name": "web-1", "template": "web-server"},
  {"name": "web-2", "template": "web-server"}, 
  {"name": "web-3", "template": "web-server"}
])

Claude: "Configure port forwarding for the first web server"
You: configure_port_forwarding("web-1", 8001, 80)
```

### Database Development

```
Claude: "Create a database VM and clone it for testing"
You: create_vm("db-main", "database-server", memory_mb=8192)
You: clone_vm("db-main", "db-test", linked=True)

Claude: "Run migrations on the test database"
You: execute_command("db-test", "sudo -u postgres psql -c 'CREATE DATABASE test;'")
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# VirtualBox Configuration
VBOX_MANAGE_PATH=VBoxManage
VBOX_DEFAULT_FOLDER=/path/to/vms

# Server Configuration  
MCP_SERVER_PORT=6274
LOG_LEVEL=INFO
DEBUG_MODE=false

# Performance Settings
OPERATION_TIMEOUT=300
MAX_CONCURRENT_OPS=3
ENABLE_CACHING=true

# Feature Flags
ENABLE_FILE_TRANSFER=true
ENABLE_COMMAND_EXECUTION=true
MOCK_MODE=false
```

### Settings (config/settings.yaml)

```yaml
server:
  name: "VirtualBox MCP Server"
  version: "1.0.0"
  timeout: 300

virtualbox:
  manage_path: "VBoxManage"
  default_folder: null
  parallel_operations: 3

templates:
  directory: "config"
  cache_enabled: true
  validation: true

networking:
  default_type: "NAT"
  port_range_start: 8000
  port_range_end: 9000
```

## 🏗 Architecture

```
virtualization-mcp/
├── server.py              # FastMCP 2.0 server
├── vbox/                  # Core VirtualBox integration
│   ├── manager.py          # VBoxManage CLI wrapper
│   ├── vm_operations.py    # VM lifecycle operations
│   ├── snapshots.py        # Snapshot management
│   ├── networking.py       # Network configuration
│   └── templates.py        # Template system
├── config/                # Configuration files
│   ├── vm_templates.yaml   # VM template definitions
│   └── settings.yaml       # Server settings
├── tests/                 # Test suite
├── docs/                  # Documentation
└── requirements.txt       # Dependencies
```

### Core Components

- **VBoxManager**: Robust CLI wrapper with error handling and validation
- **VMOperations**: Complete VM lifecycle with template support
- **SnapshotManager**: Testing workflows with rollback patterns
- **NetworkManager**: Port forwarding and connectivity management
- **TemplateManager**: YAML-based VM template system

## 🧪 Testing

### Manual Testing with MCP Inspector

```bash
# Start development server
fastmcp dev server.py

# Test in browser at http://127.0.0.1:6274
# Try these commands:
create_vm("test-vm", "minimal-linux")
start_vm("test-vm")
create_snapshot("test-vm", "clean")
stop_vm("test-vm")
delete_vm("test-vm")
```

### Automated Testing

```bash
# Run test suite
python -m pytest tests/

# Test specific component
python -m pytest tests/test_vm_operations.py

# Integration tests
python -m pytest tests/integration_tests.py
```

## 🔧 Requirements

### System Requirements

- **Python 3.11+**
- **VirtualBox 7.0+** with VBoxManage in PATH
- **FastMCP 2.10.1+**
- **Sufficient disk space** for VM templates and snapshots

### Python Dependencies

```txt
fastmcp>=2.10.1
pyyaml>=6.0
python-dotenv>=1.0.0
psutil>=5.9.0
rich>=13.0.0
loguru>=0.7.0
```

### Optional Dependencies

```txt
# Development and testing
pytest>=7.0.0
black>=23.0.0
pre-commit>=3.0.0
```

## 🚨 Error Handling

### Common Issues

**VBoxManage not found**

```
Error: VBoxManage command not found
Solution: Add VirtualBox to PATH or set VBOX_MANAGE_PATH
```

**Insufficient disk space**

```
Error: Not enough disk space for VM creation
Solution: Check available space or use linked clones
```

**VM already exists**

```
Error: VM with name 'test-vm' already exists
Solution: Use different name or delete existing VM
```

### Austrian Error Philosophy

- **Direct identification** of the problem
- **Immediate actionable solution**
- **No unnecessary complexity**
- **Clear next steps**

## 📖 Documentation

- **[API Reference](docs/API.md)** - Complete tool documentation
- **[Examples](docs/examples.md)** - Common workflow patterns
- **[Templates](docs/templates.md)** - Template customization guide
- **[Troubleshooting](docs/troubleshooting.md)** - Problem resolution

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Standards

- **Austrian efficiency**: Clean, direct, purposeful code
- **Comprehensive error handling**: Every failure path covered
- **Documentation**: Every tool and function documented
- **Testing**: Unit and integration test coverage

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[FastMCP](https://github.com/jlowin/fastmcp)** - Excellent MCP server framework
- **[VirtualBox](https://virtualbox.org)** - Robust virtualization platform
- **Austrian development philosophy** - Efficiency without complexity

---

**Built with Austrian efficiency for practical VirtualBox automation through Claude Desktop.** 🚀

*Ready for production deployment in minutes, not hours.*
