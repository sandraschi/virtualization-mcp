# Snapshot Strategy Prompt

## Purpose
Help users implement effective snapshot strategies for their virtual machines.

## Snapshot Best Practices

### When to Create Snapshots

#### Always Create Snapshots Before:
1. **Operating System Updates**
   - Major OS upgrades
   - Kernel updates
   - Critical security patches
   - Example: "Before Ubuntu 22.04 → 24.04 Upgrade"

2. **Software Installation**
   - New applications or services
   - System-wide dependencies
   - Configuration file changes
   - Example: "Before Installing Docker"

3. **Configuration Changes**
   - Network reconfiguration
   - Firewall rule changes
   - Service modifications
   - Example: "Before Network Reconfiguration"

4. **Risky Operations**
   - Testing new scripts
   - Database migrations
   - File system changes
   - Example: "Before Running Migration Script"

#### Regular Snapshot Schedule
- **Daily**: For active development VMs
- **Weekly**: For stable production-like VMs
- **Before/After**: Major milestones or deployments
- **Clean State**: After fresh installs or major configurations

### Snapshot Naming Conventions

#### Good Names (Descriptive)
- ✅ "Clean Ubuntu 22.04 Install - 2025-10-15"
- ✅ "After NodeJS + MongoDB Install"
- ✅ "Before Database Migration v2.0"
- ✅ "Working Dev Environment - All Tools Configured"
- ✅ "Pre-Production Deployment Test"

#### Poor Names (Avoid)
- ❌ "Snapshot1", "Snapshot2", "Snapshot3"
- ❌ "Test", "Backup", "Old"
- ❌ "Before", "After"
- ❌ Unnamed snapshots

### Snapshot Management

#### Cleanup Strategy
1. **Keep**: 
   - Clean install snapshots
   - Major configuration milestones
   - Last known good state
   - Pre-deployment snapshots

2. **Delete**:
   - Old test snapshots (>30 days)
   - Intermediate development snapshots
   - Failed experiment snapshots
   - Duplicate snapshots

#### Space Considerations
- Each snapshot uses disk space based on changes since last snapshot
- Linked clones save space by sharing base disk
- Delete old snapshots to reclaim space
- Monitor host disk usage regularly

### Snapshot vs Backup

#### Use Snapshots For:
- ✅ Quick rollback (seconds to restore)
- ✅ Testing and experimentation
- ✅ Development checkpoints
- ✅ Configuration milestones

#### Use Backups For:
- ✅ Disaster recovery
- ✅ Moving VMs between hosts
- ✅ Long-term archival
- ✅ Complete VM copies

## Recommended Strategies by VM Type

### Development VM
```
Clean Install
├── Dev Tools Installed
│   ├── Project A Setup
│   │   └── Feature Branch Work
│   └── Project B Setup
└── Updated Dev Tools
    └── New Framework Testing
```

**Retention**: Keep clean install + current project states, delete old feature branches

### Testing VM
```
Base Test Environment
├── Before Test Run 1
├── Before Test Run 2
└── Before Test Run 3
```

**Retention**: Keep base + latest passing test, delete old test snapshots weekly

### Production Clone
```
Production Mirror - Monthly
├── Before Change X
│   └── After Change X (if successful)
└── Before Change Y
```

**Retention**: Keep monthly mirror + recent changes, archive old mirrors to backups

## Example Interaction

**User**: "I need to update my development VM but I'm worried about breaking things"

**Assistant**:
"I'll help you create a safety snapshot before updating. This is the recommended approach:

1. **Create Pre-Update Snapshot**: I'll take a snapshot called \"Before System Update - ${current_date}\"
2. **Proceed with Updates**: You can safely update knowing you can roll back
3. **Test After Update**: Verify everything works correctly
4. **Decision Point**:
   - If successful: Keep the snapshot for 30 days, then optionally delete
   - If problems occur: Restore the snapshot immediately

Would you like me to create the pre-update snapshot now?"

