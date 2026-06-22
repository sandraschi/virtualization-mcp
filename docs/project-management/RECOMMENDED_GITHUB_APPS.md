# Recommended GitHub Apps for virtualization-mcp

A curated list of GitHub Apps to enhance development, security, and quality.

## 🔒 Security & Code Quality

### 1. **Dependabot** ✅ ALREADY INSTALLED
**What it does:** Automated dependency updates and security alerts
**Status:** ✅ Active (`.github/dependabot.yml` exists)
**Value:** 10/10 - Essential for security

### 2. **CodeQL** 🌟 HIGHLY RECOMMENDED
**What it does:** GitHub's semantic code analysis engine
**Benefits:**
- Finds security vulnerabilities automatically
- Deep semantic analysis (not just regex)
- Integrated with GitHub Security tab
- Free for public repos

**Installation:**
```yaml
# Add to .github/workflows/codeql.yml (I'll create this)
```
**Value:** 9/10 - Best-in-class security scanning

### 3. **Codecov** 🌟 HIGHLY RECOMMENDED  
**What it does:** Advanced coverage reporting and visualization
**Benefits:**
- Beautiful coverage reports
- PR comments with coverage changes
- Coverage badges
- Trend tracking over time
- Free for open source

**Installation:** https://codecov.io
**Value:** 9/10 - Essential for GLAMA Gold (80% coverage tracking)

### 4. **Snyk** 🌟 RECOMMENDED
**What it does:** Security vulnerability scanning for dependencies
**Benefits:**
- Real-time vulnerability detection
- Auto-fix PRs for security issues
- License compliance checking
- Container scanning

**Installation:** https://snyk.io
**Value:** 8/10 - Complements Dependabot

### 5. **SonarCloud** 💎 OPTIONAL
**What it does:** Comprehensive code quality analysis
**Benefits:**
- Code smells detection
- Bug detection
- Security hotspots
- Technical debt tracking
- Quality gate enforcement

**Installation:** https://sonarcloud.io
**Value:** 7/10 - Good for enterprise projects

---

## 🤖 Automation & Productivity

### 6. **GitHub Actions** ✅ ALREADY USING
**What it does:** CI/CD automation
**Status:** ✅ 13 workflows configured
**Value:** 10/10 - Core infrastructure

### 7. **Release Drafter** ✅ ALREADY CONFIGURED
**What it does:** Auto-generates release notes from PRs
**Status:** ✅ `.github/release-drafter.yml` exists
**Value:** 8/10 - Great for changelog automation

### 8. **Mergify** 💎 OPTIONAL
**What it does:** Automated PR merging with rules
**Benefits:**
- Auto-merge when CI passes
- Auto-update PRs
- Custom merge rules
- Label-based automation

**Installation:** https://mergify.com
**Value:** 6/10 - Useful for busy projects

### 9. **ImgBot** 💎 OPTIONAL
**What it does:** Automatically optimize images
**Benefits:**
- Reduces image file sizes
- Auto-submits optimization PRs
- Lossless compression
- Free for open source

**Installation:** https://imgbot.net
**Value:** 5/10 - Only if you have many images

---

## 📊 Project Management

### 10. **ZenHub** 💎 OPTIONAL
**What it does:** Agile project management inside GitHub
**Benefits:**
- Kanban boards
- Sprint planning
- Roadmap visualization
- Burndown charts

**Installation:** https://zenhub.com
**Value:** 7/10 - Great for teams

### 11. **Linear** 💎 OPTIONAL
**What it does:** Modern issue tracking
**Benefits:**
- Beautiful UI
- Fast performance
- GitHub integration
- Roadmap planning

**Installation:** https://linear.app
**Value:** 7/10 - Alternative to ZenHub

---

## 📝 Documentation

### 12. **Swimm** 💎 OPTIONAL
**What it does:** Documentation that stays in sync with code
**Benefits:**
- Code-coupled documentation
- Auto-detects outdated docs
- Developer onboarding
- Tutorial creation

**Installation:** https://swimm.io
**Value:** 6/10 - Good for complex projects

### 13. **Read the Docs** 🌟 RECOMMENDED
**What it does:** Automated documentation hosting
**Benefits:**
- Auto-builds docs from your repo
- Versioned documentation
- Search functionality
- Free for open source

**Installation:** https://readthedocs.org
**Value:** 8/10 - Perfect for API docs

---

## 🧪 Testing & Quality

### 14. **Coveralls** 💎 OPTIONAL (Alternative to Codecov)
**What it does:** Coverage tracking and reporting
**Benefits:**
- Similar to Codecov
- Good PR integration
- Free for open source

**Installation:** https://coveralls.io
**Value:** 8/10 - Choose either Codecov OR Coveralls

### 15. **DeepSource** 🌟 RECOMMENDED
**What it does:** Automated code review
**Benefits:**
- Finds bugs before code review
- Performance issues
- Security vulnerabilities
- Code style issues
- Auto-fix capabilities

**Installation:** https://deepsource.io
**Value:** 8/10 - Excellent automated reviewer

---

## 🎯 MCP-Specific Apps

### 16. **GLAMA.ai** 🌟 **HIGHLY RECOMMENDED** ⚠️ NOT YET INSTALLED
**What it does:** MCP Server Quality Certification
**Benefits:**
- Official MCP server directory listing
- Quality tier certification (Bronze/Silver/Gold/Platinum)
- Real-time quality tracking
- Community discoverability
- Automatic rescans on push

**Installation:** https://glama.ai
**Value:** 10/10 - **ESSENTIAL for MCP servers**

**Status:** ⚠️ Ready to install - See `docs/glama/GLAMA_APP_INSTALLATION.md`

---

## 🏆 RECOMMENDED INSTALLATION PRIORITY

### 🔴 HIGH PRIORITY (Install Now):

1. **GLAMA.ai** - Essential for MCP certification
2. **Codecov** - Coverage tracking for 80% goal
3. **CodeQL** - Advanced security scanning

### 🟡 MEDIUM PRIORITY (Install Soon):

4. **Snyk** - Additional security layer
5. **DeepSource** - Automated code review
6. **Read the Docs** - Professional API documentation

### 🟢 LOW PRIORITY (Consider Later):

7. **SonarCloud** - Enterprise code quality
8. **Mergify** - Auto-merge automation
9. **ZenHub/Linear** - Project management
10. **Swimm** - Living documentation

---

## 📋 CURRENT STATUS

### ✅ Already Installed/Configured:
- ✅ **Dependabot** - Dependency updates
- ✅ **GitHub Actions** - CI/CD (13 workflows!)
- ✅ **Release Drafter** - Auto-release notes

### ⚠️ Ready to Install (Prerequisites Complete):
- ⏳ **GLAMA.ai** - MCP certification
- ⏳ **Codecov** - Coverage tracking
- ⏳ **CodeQL** - Semantic security analysis

### 💡 Consider for Future:
- 💎 Snyk, DeepSource, Read the Docs
- 💎 SonarCloud, Mergify, ZenHub

---

## 🚀 Quick Installation Guide

### Install GLAMA (5 minutes):
1. Go to https://glama.ai
2. Sign in with GitHub
3. Install app to repo
4. Done! Auto-scans on push

### Install Codecov (3 minutes):
1. Go to https://codecov.io
2. Sign up with GitHub
3. Add repository
4. Token auto-configures with our workflow

### Install CodeQL (2 minutes):
1. Go to repo Settings → Security → Code scanning
2. Click "Set up code scanning"
3. Choose "CodeQL Analysis"
4. Commit the workflow file

---

## 💰 Cost Summary

| App | Free Tier | Paid Tier |
|-----|-----------|-----------|
| GLAMA | ✅ Free | - |
| Dependabot | ✅ Free | - |
| GitHub Actions | ✅ 2000 min/mo | $0.008/min |
| CodeQL | ✅ Public repos | Enterprise |
| Codecov | ✅ Open source | $10/mo+ |
| Snyk | ✅ Free tier | $52/mo+ |
| DeepSource | ✅ Open source | $30/mo+ |
| Read the Docs | ✅ Free | $50/mo |
| SonarCloud | ✅ Open source | $10/mo+ |

**For open-source projects like yours: Nearly everything is FREE!** ✅

---

## 🎯 RECOMMENDATION FOR virtualization-mcp

**Install these 3 apps THIS WEEK:**

1. **GLAMA.ai** - Get your Silver Tier badge, track to Gold
2. **Codecov** - Beautiful coverage reports & tracking
3. **CodeQL** - GitHub's best security scanner

**Total time:** ~10 minutes
**Total cost:** $0 (all free for open source)
**Value:** Huge boost to credibility and quality

---

## 📈 Expected Benefits

After installing recommended apps:

### Immediate:
- ✅ Official GLAMA Silver Tier badge
- ✅ Real-time coverage visualization
- ✅ Advanced security scanning
- ✅ PR coverage diff comments
- ✅ Professional quality signals

### Long-term:
- 📈 Clear path to GLAMA Gold visible
- 📈 Community trust increased
- 📈 Security vulnerabilities caught early
- 📈 Code quality improvements automated
- 📈 Enterprise adoption signals

---

## 🆘 Need Help?

- **GLAMA:** See `docs/glama/GLAMA_APP_INSTALLATION.md`
- **Codecov:** Their setup wizard is excellent
- **CodeQL:** GitHub has built-in setup flow

---

**Current App Score:** 7/10 (Dependabot + GitHub Actions + Release Drafter)
**With Recommended:** 10/10 (Add GLAMA + Codecov + CodeQL)

**Next Step:** Install GLAMA app to get official Silver Tier certification! 🚀

