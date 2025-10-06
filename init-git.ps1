# Git repository initialization script for VirtualBox MCP Server
# Run this script after installing Git for Windows

Write-Host "🚀 Initializing VirtualBox MCP Git Repository..." -ForegroundColor Green

# Initialize git repository
git init

# Set up initial configuration (update with your details)
# git config user.name "Your Name"
# git config user.email "your.email@example.com"

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
Write-Host "✅ Git repository initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Create repository on GitHub/GitLab" -ForegroundColor White
Write-Host "   2. Add remote: git remote add origin <repository-url>" -ForegroundColor White
Write-Host "   3. Push to remote: git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Repository ready for collaboration and deployment!" -ForegroundColor Green
