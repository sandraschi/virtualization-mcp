# Quick Start Guide - CI/CD for Virtualization-MCP

> **Get started in 5 minutes!** - Test everything works before your first release.

---

## ✅ Step 1: Install Dependencies (2 minutes)

```powershell
# In your virtualization-mcp directory
cd D:\Dev\repos\virtualization-mcp

# Install all development dependencies
uv sync --dev

# Verify installation
uv run --version
```

**Expected**: Should complete without errors and show uv version.

---

## ✅ Step 2: Run Quality Checks (3 minutes)

```powershell
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check (will show any issues)
uv run pyright

# Run tests
uv run pytest -v
```

**Expected**: 
- Formatting: No changes (or applies formatting)
- Linting: "All checks passed!"
- Type checking: May show warnings (that's OK for now)
- Tests: Most tests should pass

---

## ✅ Step 3: Test Building (2 minutes)

```powershell
# Build the package
uv build

# Validate the package
uv run twine check dist/*
```

**Expected**:
- Creates `dist/` directory
- Contains `.whl` and `.tar.gz` files
- Twine shows "PASSED"

---

## ✅ Step 4: Test Security Scans (2 minutes)

```powershell
# Run security scans
uv run bandit -r src/ --severity-level high
uv run safety scan
```

**Expected**:
- Bandit: Shows any HIGH severity issues (should be 0)
- Safety: Shows dependency vulnerabilities (should be 0)

---

## ✅ Step 5: Commit and Push (1 minute)

```powershell
# Add all changes
git add -A

# Commit
git commit -m "feat: implement CI/CD and release mechanism

- Updated all docs from advanced-memory-mcp
- Added critical build dependencies (build, twine, pyright)
- Modernized GitHub workflows to use UV
- Updated security scans to use modern commands
- Fixed all workflow issues from best practices

All workflows ready for production use!"

# Push to GitHub
git push origin master
```

**Expected**: Push should succeed

---

## ✅ Step 6: Watch GitHub Actions (2 minutes)

1. Go to: https://github.com/sandraschi/virtualization-mcp/actions
2. Watch the workflows run:
   - ✅ CI/CD Pipeline (Full)
   - ✅ Security Scanning

**Expected**: All workflows should turn green ✅

---

## 🎯 What Should Happen

### On GitHub Actions Page

You should see:
- ✅ **Lint and Format Check** - Passes
- ✅ **Test Suite** - Passes (or shows expected failures)
- ✅ **Security Scan** - Completes (findings don't block)
- ✅ **Build Package** - Creates distributable packages
- ✅ **MCPB Build** - Creates .mcpb file
- ✅ **Quality Gate** - Passes

---

## 🚀 Creating Your First Release

### Beta Release (Recommended First)

```powershell
# 1. Update versions in all 3 files:
# - pyproject.toml → version = "1.0.1b1"
# - src/virtualization_mcp/__init__.py → __version__ = "1.0.1b1"  
# - mcpb/manifest.json → "version": "1.0.1b1"

# 2. Update CHANGELOG.md with changes

# 3. Commit version bump
git add -A
git commit -m "chore: bump version to 1.0.1b1"
git push origin master

# 4. Wait for CI to pass (watch GitHub Actions)

# 5. Create and push tag
git tag -a v1.0.1b1 -m "Beta release v1.0.1b1 - CI/CD implementation"
git push origin v1.0.1b1
```

### What Happens Automatically

1. ✅ GitHub Release is created
2. ✅ `.mcpb` file is uploaded as asset
3. ✅ `.whl` file is uploaded as asset
4. ✅ `.tar.gz` file is uploaded as asset
5. ✅ Changelog is included in release notes
6. ❌ **NOT** published to PyPI (beta releases stay on GitHub)

---

## 📋 Troubleshooting

### If CI Fails

**Check**:
1. Did `uv sync --dev` complete successfully?
2. Did you commit the updated `pyproject.toml`?
3. Are workflows using `uv sync --dev` instead of `uv add --dev`?

**Fix**:
```powershell
# Pull latest changes
git pull origin master

# Reinstall dependencies
uv sync --dev

# Re-run tests locally
uv run pytest -v
```

---

### If Build Fails

**Error**: "twine: command not found"

**Fix**: 
```powershell
# Check pyproject.toml has twine in dev dependencies
grep -i twine pyproject.toml

# If not found, it should be there - pull latest changes
git pull origin master
uv sync --dev
```

---

### If Security Scan Fails

**This is OK!** Security scans are configured with `continue-on-error: true`.

- Findings are uploaded as artifacts
- Workflow continues and completes
- Review findings at your convenience

---

## 🎯 Success Checklist

After pushing, you should see:

- [x] GitHub Actions page shows green checkmarks ✅
- [x] All workflow jobs completed successfully
- [x] Artifacts uploaded (dist, mcpb-package, security-reports)
- [x] Quality gate passed
- [x] Ready to create first release!

---

## 🎉 You're Ready!

**What you have now**:
- ✅ Working CI/CD pipeline
- ✅ Automated releases on tags
- ✅ Security scanning
- ✅ Package building
- ✅ Quality gates

**Next steps**:
1. Create beta release (v1.0.1b1)
2. Test the release mechanism
3. Verify .mcpb file works in Claude Desktop
4. Make stable release (v1.0.1) when ready

---

## 📞 Need Help?

**Check these in order**:
1. `docs/github/TROUBLESHOOTING.md` - Common errors
2. `docs/github/VIRTUALIZATION_MCP_SETUP_SUMMARY.md` - What was changed
3. GitHub Actions logs - Specific error messages
4. `docs/github/WORKFLOWS.md` - Workflow templates

---

## 📚 Related Documentation

- **Setup Summary**: `docs/github/VIRTUALIZATION_MCP_SETUP_SUMMARY.md`
- **Release Checklist**: `docs/github/RELEASE_CHECKLIST.md`
- **Troubleshooting**: `docs/github/TROUBLESHOOTING.md`
- **Complete Guide**: `docs/github/COMPLETE_SETUP_GUIDE.md`

---

**Time to first green CI**: ~10 minutes  
**Time to first release**: ~15 minutes  
**Confidence level**: High! 🚀

Let's ship it! 🎉

