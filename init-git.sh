#!/bin/bash
# Git repository initialization script for VirtualBox MCP Server
# Run this script after installing Git for Windows

echo "🚀 Initializing VirtualBox MCP Git Repository..."

# Initialize git repository
git init

# Set up initial configuration (update with your details)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files to staging
git add .

# Create initial commit
git commit -m "🎉 Initial commit: VirtualBox MCP Server

✅ Complete FastMCP 2.0 implementation
✅ All core components (manager, vm_operations, snapshots, networking, templates)  
✅ 15+ MCP tools for VM management
✅ 10 production VM templates
✅ Comprehensive documentation
✅ Austrian efficiency architecture

Ready for production deployment through Claude Desktop."

# Display status
echo "✅ Git repository initialized successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Create repository on GitHub/GitLab"
echo "   2. Add remote: git remote add origin <repository-url>"
echo "   3. Push to remote: git push -u origin main"
echo ""
echo "🎯 Repository ready for collaboration and deployment!"
