# Complete VM Scenarios - Step-by-Step Guides

## Scenario 1: Setting Up a Full Stack Development Environment

### Goal
Create a complete development environment for a web application with database, backend, and frontend.

### Step-by-Step Process

#### Phase 1: Create Base VM
```
1. Create Ubuntu 22.04 VM named "fullstack-dev"
   - Memory: 8192 MB (8 GB)
   - CPUs: 4 cores
   - Disk: 60 GB
   - Network: NAT

2. Install Ubuntu Server 22.04
   - Enable SSH during installation
   - Create user account
   - Install VirtualBox Guest Additions

3. Take snapshot: "01-clean-ubuntu-install"
```

#### Phase 2: Install Development Tools
```
4. Update system:
   sudo apt update && sudo apt upgrade -y

5. Install Docker and Docker Compose:
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER

6. Install development essentials:
   sudo apt install -y git nodejs npm python3 python3-pip

7. Install VS Code Server for remote development:
   wget -O- https://aka.ms/install-vscode-server/setup.sh | sh

8. Take snapshot: "02-dev-tools-installed"
```

#### Phase 3: Configure Port Forwarding
```
9. Set up port forwarding (use network_management tool):
   - SSH: 2222 → 22
   - Frontend: 3000 → 3000 (React/Vue dev server)
   - Backend: 8000 → 8000 (Django/FastAPI)
   - Database: 5432 → 5432 (PostgreSQL)
   - Docker API: 2375 → 2375
   - VS Code Server: 8443 → 8443

10. Test connections from host machine

11. Take snapshot: "03-networking-configured"
```

#### Phase 4: Set Up Project Environment
```
12. Clone your project repository

13. Set up Docker Compose for services:
    - PostgreSQL database
    - Redis cache
    - Backend API
    - Frontend dev server

14. Create .env files with development settings

15. Test entire stack: docker-compose up

16. Take snapshot: "04-project-running"
```

#### Phase 5: Final Configuration
```
17. Configure automatic startup:
    - Enable Docker service
    - Create systemd service for your app (optional)

18. Set up VS Code Remote SSH connection

19. Configure file syncing or shared folders

20. Take snapshot: "05-production-ready"
```

### Daily Workflow
```
Morning:
  1. Start VM (headless mode)
  2. SSH in or use VS Code Remote
  3. Run docker-compose up

Coding:
  - All development in VM
  - Access via localhost:PORT on host
  - Use VS Code Remote for best experience

Evening:
  - Commit and push changes
  - Take snapshot if significant progress made
  - Save state or power off VM
```

### When Things Break
```
1. Check last snapshot
2. Review what changed since snapshot
3. Restore snapshot if needed
4. Re-apply changes one by one
5. Create new snapshot when stable
```

---

## Scenario 2: Creating a Kubernetes Testing Cluster

### Goal
Set up a multi-node Kubernetes cluster for learning and testing.

### Cluster Architecture
```
Master Node: k8s-master
  - 4 GB RAM, 2 CPUs
  - IP: 10.0.2.10
  - Role: Control plane

Worker Node 1: k8s-worker-1
  - 4 GB RAM, 2 CPUs
  - IP: 10.0.2.11
  - Role: Workload execution

Worker Node 2: k8s-worker-2
  - 4 GB RAM, 2 CPUs
  - IP: 10.0.2.12
  - Role: Workload execution

Network: Internal network "k8s-cluster"
External Access: Master has NAT adapter for kubectl access
```

### Deployment Steps

#### Step 1: Create Template VM
```
1. Create base Ubuntu 22.04 VM
2. Install Docker and kubeadm
3. Configure kernel parameters for Kubernetes
4. Disable swap
5. Take snapshot: "k8s-base-template"
```

#### Step 2: Clone for Each Node
```
6. Clone template → k8s-master (full clone)
7. Clone template → k8s-worker-1 (linked clone)
8. Clone template → k8s-worker-2 (linked clone)

Note: Linked clones save ~20 GB disk space
```

#### Step 3: Initialize Cluster
```
9. Start all VMs
10. Initialize master: kubeadm init
11. Save join command
12. Join workers to cluster
13. Install CNI plugin (Calico/Flannel)
14. Take snapshots: "cluster-initialized" on all nodes
```

#### Step 4: Configure kubectl Access
```
15. Copy kubeconfig from master
16. Set up port forwarding for kubectl (6443)
17. Test: kubectl get nodes (from host)
18. Install kubectl on host machine
```

### Testing Scenarios
```
Scenario 1: Pod Scheduling
  - Deploy sample app
  - Scale to multiple replicas
  - Observe scheduling across nodes

Scenario 2: Node Failure
  - Stop k8s-worker-1
  - Watch pods reschedule
  - Restore worker, observe rejoining

Scenario 3: Upgrades
  - Snapshot all nodes
  - Upgrade master
  - Upgrade workers one by one
  - Rollback with snapshots if issues

Scenario 4: Network Policies
  - Deploy microservices
  - Test network segmentation
  - Verify isolation

Scenario 5: Persistent Storage
  - Configure local storage
  - Test StatefulSets
  - Verify data persistence
```

### Maintenance
```
Weekly:
  - Snapshot all nodes before updates
  - Update system packages
  - Clear old snapshots

Monthly:
  - Rebuild cluster from templates
  - Test disaster recovery
  - Update Kubernetes version
```

---

## Scenario 3: Multi-Tier Application Testing

### Application: E-Commerce Platform

#### Architecture
```
Tier 1: Load Balancer (lb-vm)
  - Nginx reverse proxy
  - 1 GB RAM, 1 CPU
  - IP: 10.0.2.5
  - Public-facing (NAT + Port 80→8080)

Tier 2: Application Servers (app-vm-1, app-vm-2)
  - Node.js/Django application
  - 4 GB RAM, 2 CPUs each
  - IPs: 10.0.2.10, 10.0.2.11
  - Connected to internal networks

Tier 3: Cache Layer (cache-vm)
  - Redis instance
  - 2 GB RAM, 1 CPU
  - IP: 10.0.2.20
  - Internal network only

Tier 4: Database (db-vm)
  - PostgreSQL with replication
  - 8 GB RAM, 4 CPUs
  - IP: 10.0.2.30
  - Dedicated storage controller

Tier 5: Queue System (queue-vm)
  - RabbitMQ or Redis Queue
  - 2 GB RAM, 2 CPUs
  - IP: 10.0.2.40
```

#### Network Design
```
Networks:
  - frontend-net: lb-vm ↔ app-vm-*
  - backend-net: app-vm-* ↔ cache-vm, db-vm, queue-vm
  - admin-net: Management access to all VMs

Security:
  - Only lb-vm exposed to host
  - Database accessible only from app-vms
  - No direct external access to internal services
```

#### Deployment Process
```
Phase 1: Infrastructure (20 minutes)
  1. Create all VMs from templates
  2. Configure static IPs on each VM
  3. Test network connectivity between tiers
  4. Take snapshot: "infrastructure-ready"

Phase 2: Service Installation (30 minutes)
  5. Install Nginx on lb-vm
  6. Install application on app-vms
  7. Install Redis on cache-vm
  8. Install PostgreSQL on db-vm
  9. Install RabbitMQ on queue-vm
  10. Take snapshots: "services-installed"

Phase 3: Configuration (20 minutes)
  11. Configure Nginx load balancing
  12. Configure app database connections
  13. Set up Redis caching
  14. Configure queue workers
  15. Take snapshots: "configured"

Phase 4: Application Deployment (15 minutes)
  16. Deploy application code to app-vms
  17. Run database migrations on db-vm
  18. Start all services
  19. Test complete workflow
  20. Take snapshots: "deployed"
```

#### Testing Scenarios
```
1. Load Testing:
   - Snapshot all VMs
   - Run load test against lb-vm
   - Monitor resource usage
   - Restore if anything breaks

2. Failure Testing:
   - Stop app-vm-1, verify lb routes to app-vm-2
   - Stop db-vm, verify app handles gracefully
   - Stop cache-vm, verify fallback to database

3. Scaling Testing:
   - Clone app-vm-2 → app-vm-3
   - Add to load balancer pool
   - Verify traffic distribution
   - Test removing from pool

4. Security Testing:
   - Attempt to connect directly to db-vm (should fail)
   - Test SQL injection (in test data)
   - Verify encrypted connections
   - Test firewall rules

5. Backup/Recovery Testing:
   - Export entire environment
   - Delete all VMs
   - Restore from backup
   - Verify everything works
```

---

## Scenario 4: Continuous Integration Pipeline

### Goal
Create an isolated CI/CD environment for testing builds.

#### VM Configuration
```
CI Server (jenkins-vm):
  - Ubuntu Server 22.04
  - 4 GB RAM, 2 CPUs
  - 80 GB disk (for build artifacts)
  - NAT network
  - Port forward: 8080→8080 (Jenkins UI)

Build Agent 1 (build-agent-linux):
  - Ubuntu Server 22.04
  - 8 GB RAM, 4 CPUs
  - 40 GB disk
  - Internal network + NAT
  - Docker installed

Build Agent 2 (build-agent-windows):
  - Windows Server 2022
  - 8 GB RAM, 4 CPUs
  - 60 GB disk
  - Internal network + NAT
  - Visual Studio Build Tools

Artifact Repository (artifact-vm):
  - Ubuntu Server 22.04
  - 2 GB RAM, 1 CPU
  - 200 GB disk
  - Internal network
  - Runs Nexus or Artifactory
```

#### Setup Process
```
1. Install Jenkins on jenkins-vm
2. Configure Jenkins agents on build VMs
3. Set up shared storage or NFS for artifacts
4. Configure build pipelines
5. Take snapshots of each VM: "ci-configured"

Pipeline Example:
  1. Code commit triggers Jenkins
  2. Jenkins assigns build to appropriate agent
  3. Agent pulls code, runs tests
  4. If tests pass, build artifacts
  5. Upload artifacts to artifact-vm
  6. Deploy to test environment (another set of VMs)
  7. Run integration tests
  8. Snapshot if all tests pass
```

#### Benefits
```
- Complete isolation from host machine
- Parallel builds on multiple agents
- Easy to reset if builds corrupt environment
- Can snapshot "working CI" state
- Safe to experiment with pipeline configs
- Can clone entire CI environment for staging
```

---

## Scenario 5: Database Migration Testing

### Challenge
Test database migration from MySQL to PostgreSQL safely.

#### Environment Setup
```
Source DB VM (mysql-source):
  - Ubuntu Server
  - 4 GB RAM, 2 CPUs
  - MySQL 8.0
  - Current production data (copied)
  - Snapshot: "production-clone"

Target DB VM (postgres-target):
  - Ubuntu Server
  - 4 GB RAM, 2 CPUs
  - PostgreSQL 15
  - Empty database
  - Snapshot: "fresh-postgres"

Migration Tool VM (migration-vm):
  - Ubuntu Desktop (for GUI tools)
  - 2 GB RAM, 2 CPUs
  - pgLoader or custom migration scripts
  - Connected to both DB VMs

Application Test VM (app-test):
  - Clone of production app
  - Tests against PostgreSQL
  - Internal network access to postgres-target
```

#### Migration Process
```
Phase 1: Preparation
  1. Snapshot all VMs: "pre-migration"
  2. Backup MySQL data
  3. Analyze schema differences
  4. Write migration scripts

Phase 2: Schema Migration
  5. Create PostgreSQL schema
  6. Test with sample data
  7. Snapshot postgres-target: "schema-ready"

Phase 3: Data Migration
  8. Run migration tools
  9. Verify data integrity
  10. Check data counts and relationships
  11. Snapshot postgres-target: "data-migrated"

Phase 4: Application Testing
  12. Configure app-test to use PostgreSQL
  13. Run full test suite
  14. Performance testing
  15. If issues: restore snapshot, fix, retry

Phase 5: Validation
  16. Compare data between MySQL and PostgreSQL
  17. Run production-like queries
  18. Verify all features work
  19. Performance benchmarking

Phase 6: Cutover Planning
  20. Document exact steps
  21. Time each phase
  22. Create rollback plan
  23. Snapshot: "ready-for-production"
```

#### Rollback Strategy
```
If migration fails at any point:
  1. Stop all VMs
  2. Restore to "pre-migration" snapshots
  3. Analyze what went wrong
  4. Fix issues in migration scripts
  5. Restore to "pre-migration" again
  6. Retry migration

Benefits of VM approach:
  - Unlimited retry attempts
  - No impact on production
  - Can test rollback procedure
  - Perfect for training team
```

---

## Scenario 6: Security Compliance Testing

### Goal
Test application against security compliance requirements (OWASP, PCI-DSS, etc.)

#### Test Environment
```
Application VM (app-security-test):
  - Clone of production app
  - All security features enabled
  - Connected to test database

Security Scanner VM (scanner-vm):
  - Kali Linux
  - Security tools installed
  - Internal network only

Monitoring VM (monitor-vm):
  - SIEM/log aggregation
  - Intrusion detection
  - Traffic analysis
```

#### Testing Phases
```
Phase 1: Vulnerability Scanning
  1. Snapshot all VMs: "pre-scan"
  2. Run automated scanners (OWASP ZAP, Nessus)
  3. Document findings
  4. Restore snapshots

Phase 2: Penetration Testing
  5. Snapshot: "pre-pentest"
  6. Manual penetration testing
  7. Attempt common attacks (SQL injection, XSS, etc.)
  8. Document successful exploits
  9. Restore snapshots

Phase 3: Remediation Testing
  10. Apply security fixes to app
  11. Snapshot: "fixes-applied"
  12. Re-run all tests
  13. Verify fixes work
  14. Document improvements

Phase 4: Compliance Verification
  15. Run compliance checkers
  16. Generate compliance reports
  17. Create evidence package
  18. Final snapshot: "compliance-verified"
```

---

## Scenario 7: Performance Testing and Optimization

### Goal
Optimize application performance through systematic testing.

#### Test Environment
```
App VM (perf-test-app):
  - Start with production-like specs
  - Monitoring tools installed
  - APM agent configured

Database VM (perf-test-db):
  - Production data volume (anonymized)
  - Query logging enabled
  - Performance monitoring

Load Generator VM (load-gen):
  - JMeter or Locust
  - Multiple network adapters
  - Snapshot before each test run
```

#### Testing Methodology
```
Baseline Test:
  1. Snapshot all VMs: "baseline-config"
  2. Run load test with current config
  3. Record metrics (response time, throughput, errors)
  4. Save results

Optimization Iteration:
  5. Make ONE change (e.g., increase worker threads)
  6. Snapshot: "change-{{description}}"
  7. Run same load test
  8. Compare results
  9. If better: keep change, if worse: restore snapshot
  10. Repeat steps 5-9 for each optimization

Changes to Test:
  - Application: Worker threads, connection pools, caching
  - Database: Indexes, query optimization, connection limits
  - System: CPU allocation, memory, disk I/O
  - Network: MTU size, adapter type, throughput limits

Best Practice:
  - Change ONE thing at a time
  - Snapshot before each change
  - Run same test consistently
  - Document all changes
  - Keep successful snapshots
  - Build up optimization incrementally
```

---

## Scenario 8: Disaster Recovery Drills

### Goal
Practice disaster recovery to ensure business continuity.

#### Scenario Setup
```
Production Simulation:
  - 5 VMs mimicking production
  - All services running
  - Sample data loaded
  - Snapshot: "production-running"

Backup Storage:
  - Export all VMs to external drive
  - Document backup location
  - Test restore procedure
```

#### Disaster Scenarios to Practice

##### Scenario A: Database Corruption
```
1. Snapshot: "pre-disaster"
2. Simulate corruption (corrupt database file)
3. Attempt to start database (fails)
4. PRACTICE: Restore from last good snapshot
5. Verify data integrity
6. Document recovery time
7. Restore to "pre-disaster" for next drill
```

##### Scenario B: Complete VM Loss
```
1. Delete application VM (simulate hardware failure)
2. PRACTICE: Restore from backup export
3. Reconfigure networking
4. Verify application works
5. Document recovery time and steps
6. Identify improvements needed
```

##### Scenario C: Ransomware Attack
```
1. Snapshot: "pre-attack"
2. Simulate file encryption
3. PRACTICE: 
   - Identify attack
   - Isolate affected VMs (disconnect network)
   - Restore from clean snapshot
   - Verify no persistence
4. Document response procedure
5. Train team on steps
```

#### Drill Schedule
```
Weekly: Simple recovery (restore single VM snapshot)
Monthly: Complex recovery (restore multi-VM environment)
Quarterly: Full disaster recovery (rebuild from backups)

Benefits:
  - Team knows exactly what to do
  - Documented procedures tested
  - Recovery time objectives validated
  - Gaps in backup strategy identified
```

---

## Scenario 9: Development Team Onboarding

### Goal
Quickly onboard new developers with consistent environments.

#### Template Strategy
```
Create "Developer Workstation" Template:
  1. Ubuntu Desktop or Windows 10/11
  2. All development tools pre-installed
  3. IDE configured with team settings
  4. Git configured (except user credentials)
  5. Docker and required services
  6. Project repository cloned
  7. Sample data loaded

Snapshot: "onboarding-template"
```

#### Onboarding Process (15 minutes!)
```
For each new developer:

1. Clone template → "dev-{{developer-name}}"
   (3 minutes - linked clone, very fast)

2. Developer first boot:
   - Set their git credentials
   - Generate SSH keys
   - Configure IDE preferences
   - Test build and run

3. Take snapshot: "{{developer-name}}-configured"

4. Developer starts coding immediately!

Benefits vs. Manual Setup:
  - Hours of setup → 15 minutes
  - Consistent environment for everyone
  - No "works on my machine" issues
  - Easy to update template for whole team
  - New developer productive same day
```

#### Team Template Updates
```
When updating tools/dependencies:

1. Start from template VM
2. Apply updates
3. Test thoroughly
4. Take snapshot: "template-v{{version}}"
5. Announce to team
6. Each developer:
   - Commits their work
   - Deletes old VM
   - Clones new template
   - Restores their personal settings
   - Continues work

Minimal disruption, maximum consistency!
```

---

## Scenario 10: Conference/Workshop VM Distribution

### Goal
Distribute pre-configured VMs to workshop participants.

#### Workshop VM Preparation
```
1. Create base VM with all workshop materials
   - Ubuntu or Windows (workshop choice)
   - All required software installed
   - Workshop code/examples pre-loaded
   - Sample data included
   - Helpful shortcuts on desktop

2. Configure for easy use:
   - Auto-login enabled (for workshop)
   - Clear desktop instructions
   - All tools accessible from desktop
   - Network set to NAT (works anywhere)

3. Optimize for distribution:
   - Compact disk image (removes unused space)
   - Remove temporary files
   - Clear logs and history
   - Take snapshot: "workshop-ready"

4. Export as OVF/OVA:
   - Use VBoxManage export command
   - Include manifest for verification
   - Compress for distribution
   - Test import on clean machine
```

#### Distribution Methods
```
Option 1: USB Drives
  - Copy OVA to USB drives
  - Include VirtualBox installer
  - Provide printed quick start guide

Option 2: Cloud Download
  - Upload to S3/Google Drive
  - Provide download link
  - Include checksum for verification

Option 3: Pre-import for Participants
  - Import VMs on all workshop computers
  - Participants just need to start VM
  - Fastest option for large workshops
```

#### Workshop Day Workflow
```
1. Participants import VM (5 minutes)
   - File → Import Appliance
   - Accept defaults
   - Wait for import

2. Participant starts VM
   - Desktop shows clear instructions
   - All tools ready to use
   - Internet access works (NAT)

3. Workshop proceeds smoothly
   - Everyone has identical environment
   - No "installation failed" issues
   - Instructor can demo knowing exact setup

4. Post-workshop
   - Participants keep VM for practice
   - Can reset with snapshot
   - Can export notes/work before deleting
```

---

## Resource Estimation Guide

### Small Project (1-2 developers)
```
Total VMs: 2-3
Total RAM allocated: 8-12 GB
Total Disk: 100-150 GB
Host Requirements: 16 GB RAM, 200 GB free disk

Setup:
  - 1 Development VM per developer
  - 1 Shared test/database VM
  - All linked clones where possible
```

### Medium Project (5-10 developers)
```
Total VMs: 10-15
Total RAM allocated: 30-40 GB
Total Disk: 300-400 GB
Host Requirements: 64 GB RAM, 500 GB free disk

Setup:
  - 1 Development VM per developer
  - 3-VM test environment (web, app, db)
  - 1 CI/CD server
  - 1 Staging environment (clone of test)
  - Templates for common configurations
```

### Large Project (10+ developers)
```
Consider:
  - Dedicated VirtualBox host server
  - Remote access to VMs
  - Centralized template management
  - Automated VM provisioning
  - Regular cleanup of old VMs
  - Use of linked clones extensively
```

---

## Advanced Patterns

### The "Time Machine" Pattern
```
Use Case: Need to test code at different points in time

Setup:
  1. Create base VM with application
  2. Take snapshot every significant change
  3. Name snapshots with date and description
  4. Can boot any historical state instantly

Benefits:
  - Debug when regression was introduced
  - Test fixes against old configurations
  - Verify upgrades don't break old data
  - Historical compliance verification
```

### The "Matrix Testing" Pattern
```
Use Case: Test across multiple OS/version combinations

Setup:
  - Create template for each OS/version
  - Use linked clones for test runs
  - Automate test execution across all
  - Snapshot before each test run

Example Matrix:
  - Ubuntu 20.04, 22.04, 24.04
  - Python 3.8, 3.9, 3.10, 3.11, 3.12
  - 15 combinations = 15 linked clone VMs
  
Total disk usage: ~25 GB (vs 375 GB for full clones!)
```

### The "Progressive Enhancement" Pattern
```
Use Case: Build up complex configuration step-by-step

Setup:
  1. Base OS → Snapshot "01-base"
  2. Add security hardening → Snapshot "02-hardened"
  3. Install monitoring → Snapshot "03-monitored"
  4. Add application → Snapshot "04-app"
  5. Configure HA → Snapshot "05-ha"
  6. Production ready → Snapshot "06-production"

Benefits:
  - Can start from any stage
  - Easy to test individual components
  - Clear progression of changes
  - Educational for new team members
  - Can branch at any point
```

---

## Common Mistakes to Avoid

### ❌ Don't:
1. Run too many VMs simultaneously (RAM overload)
2. Forget to take snapshots before risky changes
3. Keep VMs running when not needed (resource waste)
4. Let snapshot trees grow too deep (performance impact)
5. Store VMs on slow drives (use SSD if possible)
6. Ignore disk space warnings
7. Run VMs without Guest Additions
8. Use GUI mode for automated tasks
9. Forget to configure port forwarding before headless mode
10. Delete VMs without exporting if you might need them

### ✅ Do:
1. Snapshot before every major change
2. Use headless mode for servers
3. Use linked clones when appropriate
4. Document your VM configurations
5. Regular backup exports of important VMs
6. Use templates for repeated deployments
7. Monitor host resources
8. Clean up old snapshots regularly
9. Use descriptive VM and snapshot names
10. Test your backup/restore procedures

---

## Quick Reference: When to Use What

**Snapshot**: Quick save point, testing changes, before updates
**Clone**: New independent VM, testing different configs
**Export**: Backup, distribution, migration to another host
**Template**: Repeated deployments, team consistency, quick starts
**Linked Clone**: Multiple test VMs, save disk space, temporary tests

---

Ready to implement any of these scenarios? I can guide you through each step!

