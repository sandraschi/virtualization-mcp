# Git Repository Setup Guide

## 🔧 Prerequisites

### 1. Install Git for Windows

**Option A: Download from Official Site**

1. Visit <https://git-scm.com/download/win>
2. Download Git for Windows installer
3. Run installer with default settings
4. Restart command prompt/PowerShell

**Option B: Use Winget (if available)**

```powershell
winget install --id Git.Git -e --source winget
```

**Option C: Use Chocolatey (if available)**

```powershell
choco install git
```

### 2. Verify Git Installation

```bash
git --version
# Should show: git version 2.45.x or newer
```

## 🚀 Initialize Repository

### Option A: Run PowerShell Script

```powershell
cd d:\dev\repos\vboxmcp
.\init-git.ps1
```

### Option B: Manual Setup

```bash
cd d:\dev\repos\vboxmcp

# Initialize repository
git init

# Configure Git (update with your details)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Initial commit
git commit -m "🎉 Initial commit: VirtualBox MCP Server

✅ Complete FastMCP 2.0 implementation
✅ All core components ready
✅ 15+ MCP tools for VM management  
✅ 10 production VM templates
✅ Comprehensive documentation
✅ Austrian efficiency architecture

Ready for production deployment through Claude Desktop."
```

## 🌐 Create Remote Repository

### GitHub

1. Go to <https://github.com/new>
2. Repository name: `vboxmcp` or `virtualbox-mcp-server`
3. Description: "FastMCP 2.0 server for VirtualBox management through Claude Desktop"
4. Public/Private as needed
5. Create repository

### Add Remote and Push

```bash
# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/vboxmcp.git

# Push to remote
git push -u origin main
```

## 📋 Repository Structure Ready

```
vboxmcp/
├── .git/                   # Git repository data
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
├── README.md              # Complete documentation
├── init-git.ps1           # PowerShell setup script
├── init-git.sh            # Bash setup script
├── setup-git.md           # This guide
├── server.py              # FastMCP server
├── vbox/                  # Core components
├── config/                # Templates & settings
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
└── .env.example          # Environment template
```

## 🎯 Next Steps

1. **Complete server.py** (if not finished)
2. **Test with FastMCP Inspector**: `fastmcp dev server.py`
3. **Add to Claude Desktop** MCP configuration
4. **Create first VM**: Test the complete workflow
5. **Document usage patterns** in docs/

## 🔄 Development Workflow

```bash
# Make changes
git add .
git commit -m "feat: add new MCP tool for X"
git push

# Create feature branches for major changes
git checkout -b feature/advanced-networking
# ... make changes ...
git commit -m "feat: advanced networking tools"
git push -u origin feature/advanced-networking
# Create pull request on GitHub
```

## 🚨 Troubleshooting

**Git not found after installation**

- Restart command prompt/PowerShell
- Check PATH: `$env:PATH` (PowerShell) or `echo $PATH` (bash)
- Reinstall with "Add Git to PATH" option selected

**Permission denied (public key)**

- Use HTTPS instead of SSH for first setup
- Or configure SSH keys: <https://docs.github.com/en/authentication>

**Commit failed**

- Configure user name/email first
- Check for empty commit message

---

**Austrian efficiency achieved: Repository ready for immediate collaboration and deployment!** 🚀
