# Advanced VM Workflows Prompt

## Purpose
Guide users through complex multi-step virtualization workflows and advanced use cases.

## Advanced Workflow Templates

### 1. Multi-Tier Application Deployment

**Scenario**: Deploy a 3-tier web application (Web → App → Database)

**Architecture**:
```
Web Tier (web-server)
- Ubuntu Server
- nginx/Apache
- NAT + Internal "app-net"
- Port forward: 8080→80

App Tier (app-server)  
- Ubuntu Server
- Node.js/Python/Java
- Internal "app-net" + Internal "db-net"

Database Tier (db-server)
- Ubuntu Server
- PostgreSQL/MySQL
- Internal "db-net" only
```

**Workflow**:
1. Create internal networks: "app-net", "db-net"
2. Create database VM (most isolated)
3. Create app server VM (middle tier)
4. Create web server VM (public-facing)
5. Configure each VM with appropriate network adapters
6. Install and configure services
7. Create "Initial Deployment" snapshots for all VMs
8. Test end-to-end connectivity
9. Create "Working Configuration" snapshots

**Benefits**:
- Network isolation for security
- Easy rollback with snapshots
- Can clone entire environment for staging
- Proper separation of concerns

### 2. Development Environment Cloning Strategy

**Scenario**: Create isolated development environments for each project

**Base Template Approach**:
1. Create "Dev-Base" VM with all common tools
2. Install OS, IDE, Git, Docker, etc.
3. Configure and optimize
4. Create snapshot "Clean Dev Base"
5. Export as template

**Per-Project Deployment**:
1. Deploy template → "Project-A-Dev"
2. Configure project-specific tools
3. Create "Project A Ready" snapshot
4. Clone for team members: "Project-A-Dev-Alice", "Project-A-Dev-Bob"

**Advantages**:
- Consistent environments across team
- Fast project onboarding (minutes, not hours)
- Isolated project dependencies
- Easy cleanup when project ends

### 3. CI/CD Testing Pipeline

**Scenario**: Automated testing in clean VMs

**Infrastructure**:
```
Test Controller (Host Machine)
├── Base Test VM (template)
│   ├── Clean OS install
│   ├── Test frameworks installed
│   └── Snapshot: "Test Base"
│
├── Test Run 1 (linked clone)
│   ├── Deploy application
│   ├── Run tests
│   └── Delete after completion
│
└── Test Run 2 (linked clone)
    ├── Deploy application
    ├── Run tests
    └── Delete after completion
```

**Workflow**:
1. Create base test VM with test frameworks
2. For each test run:
   - Clone base VM (linked clone for speed)
   - Start cloned VM
   - Deploy application to test
   - Run automated tests
   - Collect results
   - Delete clone
3. Repeat for each test suite

**Benefits**:
- Clean test environment every time
- Parallel testing (multiple clones)
- Fast (linked clones share base disk)
- Reproducible results

### 4. Security Testing Lab

**Scenario**: Isolated environment for security research and penetration testing

**Lab Setup**:
```
Security Lab Network (internal "sec-lab")
├── Attack VM (Kali Linux)
│   ├── Security tools installed
│   └── Snapshot: "Clean Kali"
│
├── Target VMs (various)
│   ├── Vulnerable app servers
│   ├── Different OS versions
│   └── Snapshots before each test
│
└── Monitoring VM (optional)
    ├── Network monitoring tools
    └── Log collection
```

**Safety Measures**:
- All VMs on isolated internal network ONLY
- No external network access
- Host-only adapter for controlled access
- Regular snapshots for quick reset
- Dedicated host machine recommended

**Workflow**:
1. Set up isolated internal network
2. Deploy target VMs (what you're testing)
3. Deploy attack VM (Kali Linux)
4. Create snapshots of all VMs
5. Conduct security testing
6. Restore all VMs to snapshots after each test
7. Document findings

### 5. Disaster Recovery and Business Continuity

**Scenario**: Production VM backup and recovery strategy

**Strategy**:
```
Production VM
├── Daily Snapshots (keep last 7)
├── Weekly Snapshots (keep last 4)
├── Monthly Backups (full export, keep last 12)
└── Before-Change Snapshots (keep until verified)
```

**Implementation**:
1. **Automated Daily Snapshots**:
   - Snapshot name: "Daily-${date}"
   - Taken during low-usage period
   - Automatically delete >7 days old

2. **Weekly Full Backups**:
   - Export complete VM to external storage
   - Include all snapshots
   - Verify backup integrity
   - Store off-site copy

3. **Before-Change Snapshots**:
   - Create before any configuration change
   - Keep until change verified stable (7-30 days)
   - Document what change was made

4. **Monthly Archives**:
   - Full VM export
   - Long-term storage
   - Compliance/audit requirements

**Recovery Procedures**:
- **Minor Issue**: Restore to yesterday's snapshot (seconds)
- **Major Issue**: Restore to last weekly snapshot (minutes)
- **Complete Failure**: Import monthly backup (30-60 minutes)

### 6. Development→Staging→Production Pipeline

**Scenario**: Progressive VM deployment strategy

**Infrastructure**:
```
Development VMs (local VirtualBox)
- Full resources for development
- Frequent snapshots
- Experimental configurations

→ Staging VMs (local VirtualBox)
  - Mirror production configuration
  - Integration testing
  - Performance validation
  - Weekly snapshots

→ Production (actual deployment)
  - Final validated configuration
  - Minimal changes
  - Comprehensive backups
```

**Workflow**:
1. Develop features in dev VM
2. Create snapshot when feature complete
3. Clone to staging VM
4. Test in staging (matching production)
5. If tests pass, export VM configuration
6. Deploy to production
7. Keep staging VM for future testing

## Advanced Techniques

### Linked Clones for Space Efficiency
```
Base VM (40 GB)
├── Linked Clone 1 (only 2 GB - stores differences)
├── Linked Clone 2 (only 1.5 GB)
└── Linked Clone 3 (only 3 GB)

Total space: 40 + 2 + 1.5 + 3 = 46.5 GB
vs Full Clones: 40 + 40 + 40 + 40 = 160 GB

Savings: 70% disk space!
```

### Snapshot Tree Management
```
Clean Install
├── Development Setup
│   ├── Project A
│   │   ├── Feature 1
│   │   └── Feature 2
│   └── Project B
└── Production Mirror
    ├── Pre-Update 1
    └── Pre-Update 2
```

Strategy:
- Keep main branches (Clean Install, Production Mirror)
- Delete old feature branches when merged
- Flatten tree periodically by merging snapshots

### Network Isolation Strategies
```
Untrusted Network (isolated internal)
- No external access
- Malware analysis
- Suspicious downloads

Semi-Trusted Network (internal + controlled NAT)
- Limited external access
- Development work
- Monitored connections

Trusted Network (full access)
- Production VMs
- Validated applications
- Standard security measures
```

## Example Interaction

**User**: "I need to set up a complete development environment with database and web server for my team"

**Assistant**:
"I'll help you set up a professional team development environment.

**Recommended Architecture**:

**1. Base Development VM** (Template)
- Ubuntu 22.04 Desktop
- 4 GB RAM, 2 CPUs, 60 GB disk
- Shared tools: Git, Docker, IDE, utilities
- Snapshot: \"Team Dev Base v1.0\"

**2. Database VM** (Shared Resource)
- Ubuntu Server
- 4 GB RAM, 2 CPUs, 40 GB disk
- PostgreSQL + MySQL
- Internal network \"team-dev-net\"
- Static IP: 10.0.2.50
- Daily snapshots

**3. Per-Developer VMs** (Clones of Base)
- Clone \"Dev-Base\" for each team member
- Host-Only network for SSH access
- Internal network \"team-dev-net\" (shared database access)
- Each developer gets unique ports for services

**Network Configuration**:
```
Each Dev VM:
  Adapter 1: NAT (internet)
    Port Forwards: 8080+N→8080, 3000+N→3000 (N=developer#)
  Adapter 2: Internal \"team-dev-net\"
    Static IP: 10.0.2.10+N
  Adapter 3: Host-Only
    Static IP: 192.168.56.10+N (SSH access)

Database VM:
  Adapter 1: Internal \"team-dev-net\"
    Static IP: 10.0.2.50 (accessible to all dev VMs)
```

**Setup Steps**:
1. Create base development VM
2. Create shared database VM
3. Clone base VM for each developer
4. Configure unique network settings for each
5. Create setup documentation
6. Take snapshots of all VMs

**Benefits**:
✅ Consistent development environments
✅ Shared database reduces resource usage
✅ Easy to add new team members (clone base)
✅ Isolated work (won't break each other's code)
✅ Quick reset with snapshots

Would you like me to start creating this infrastructure?"

