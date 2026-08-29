# Virtualization MCP - User Guide and Tutorials

Version 1.4.0. This guide is the companion to system.md. It walks through installing and
configuring the server, then gives concrete tutorials for the workflows people actually run:
creating and cloning VMs, snapshots, networking, storage, isolated code execution, Windows
Sandbox, and the safe experimental pattern.

## 1. Introduction

Virtualization MCP turns natural language into virtual machine and sandbox operations. You
ask an assistant to "spin up a disposable Ubuntu VM, snapshot it, run a test, and roll it
back if it fails" and the server drives VirtualBox, Hyper-V, libvirt/KVM, Proxmox VE, Docker,
and Windows Sandbox to do it. It is a control plane: one set of tools, one result shape, many
backends.

This guide assumes you have a hypervisor installed (VirtualBox is the default), Python 3.12+,
and uv. Windows users may also use Hyper-V or Windows Sandbox; Linux/WSL2 users may use
libvirt/KVM; Proxmox users configure a remote host.

## 2. Installation and First Run

### 2.1 Verify the hypervisor

VirtualBox is the default. Confirm VBoxManage is reachable:

```powershell
VBoxManage --version
```

If it is not on PATH, set VBOX_MANAGE_PATH (or VBOXMANAGE_PATH) to the executable.

### 2.2 Install the server

```powershell
git clone https://github.com/sandraschi/virtualization-mcp
cd virtualization-mcp
uv sync
```

### 2.3 Run it

For an AI-only MCP server (Claude Desktop / Cursor):

```powershell
uv run virtualization-mcp
```

For HTTP transport:

```powershell
uv run virtualization-mcp --transport http
```

The server then listens on the MCP port (default 10702, alias VIRTUALIZATION_MCP_PORT).

### 2.4 Register in an MCP host

Add to your MCP host config (or use the packaged .mcpb bundle):

```json
"mcpServers": {
  "virtualization-mcp": { "command": "uv", "args": ["run", "virtualization-mcp"] }
}
```

### 2.5 Verify the server is up

Call system_management with action=vbox_version to confirm VirtualBox is reachable, and
system_management with action=host_info to see the host. Then use info_tools action=list_tools
to discover the surface.

## 3. Configuration Reference

Most settings come from environment variables (see system.md section 4). The ones you are
most likely to change:

- VBOX_MANAGE_PATH: VirtualBox executable if not on PATH.
- DEFAULT_VM_FOLDER: where VMs live.
- PROXMOX_HOST / PROXMOX_USER / PROXMOX_PASSWORD: to activate Proxmox remote management.
- TOOL_MODE: production (portmanteau, default) or testing (adds 60+ individual tools).
- DEFAULT_MEMORY_MB, DEFAULT_DISK_GB, DEFAULT_OS_TYPE: VM defaults.
- COMMAND_TIMEOUT, VM_START_TIMEOUT, SNAPSHOT_TIMEOUT: operation timeouts.

## 4. Tutorial 1 - List and Inspect VMs

Goal: see what VMs exist and their state.

1. Call vm_management with action=list to see all VMs.
2. Call action=info for a specific VM's detail.
3. Call system_management action=host_info to see host capacity.
4. Use info_tools action=list_tools to confirm what is available.

## 5. Tutorial 2 - Create a VM

Goal: provision a new VM.

1. Call system_management action=ostypes to get valid os_type values.
2. Call vm_management with action=create, vm_name, os_type, memory_mb, and disk_size_gb.
3. Call storage_management action=list_controllers to find a controller, then
   action=attach_disk to attach the created disk.
4. Call network_management action=configure_adapter to set networking (NAT by default).
5. Call vm_management action=start to boot it headless.

## 6. Tutorial 3 - Clone a VM

Goal: make repeatable copies from a base VM.

1. Provision a base VM once and verify it boots.
2. Call vm_management with action=clone, source_vm, and new_vm_name.
3. Repeat the clone for each task that needs an isolated environment.
4. Delete the clone when done.

## 7. Tutorial 4 - Snapshot and Restore

Goal: protect against a destructive operation.

1. Before risky work, call snapshot_management with action=create, vm_name, snapshot_name
   (for example pre-work-clean), and a description.
2. Do the work.
3. If it failed, call action=restore with the same vm_name and snapshot_name.
4. When finished, call action=delete to remove the snapshot.
5. Call action=list to see the snapshot tree.

## 8. Tutorial 5 - Configure Networking

Goal: set up a VM's network.

1. Call network_management action=list_networks to see host-only networks.
2. To create one, call action=create_network with a name, ip, and netmask.
3. Call action=configure_adapter with adapter_slot and network_type (nat, bridged, hostonly,
   internal, generic, natnetwork).
4. Call action=list_adapters to confirm the change.

## 9. Tutorial 6 - Manage Storage

Goal: add a disk to a VM.

1. Call storage_management action=list_controllers for the VM.
2. If none, call action=create_controller with a controller_type (ide, sata, scsi, sas, usb,
   pcie).
3. Call action=create_disk with disk_name and disk_size_gb.
4. Call action=attach_disk to attach it.
5. Call action=list_disks to confirm.

## 10. Tutorial 7 - Run Throwaway Code

Goal: execute a quick script in an isolated container.

1. Call sandbox_management with action=execute_code, code, language (python, javascript,
   bash), and a timeout.
2. Set network_enabled=true if the code needs the network.
3. Read the output and exit code.
4. No cleanup needed; the container is ephemeral.

## 11. Tutorial 8 - Run Stateful Code in a Session

Goal: run code that persists state across calls.

1. Call sandbox_management action=session_create (image defaults to python:3.13-slim).
2. Call action=session_write_file to put code in the session.
3. Call action=session_run to execute.
4. Call action=session_read_file to read outputs.
5. Call action=session_destroy to clean up.
6. Use action=session_list to see active sessions.

## 12. Tutorial 9 - Launch a Windows Sandbox

Goal: get an ephemeral Windows environment.

1. Call sandbox_management action=win_sandbox_launch_devinfra (or
   win_sandbox_launch_consumer) to bring one up.
2. Call action=win_sandbox_status to check it.
3. When finished, call action=win_sandbox_terminate to tear it down.

## 13. Tutorial 10 - The Safe Experimental Pattern

Goal: run risky work with a rollback path.

1. Create a disposable VM (Tutorial 2).
2. Snapshot it (Tutorial 4).
3. Do the work.
4. Evaluate; restore the snapshot if it failed.
5. Stop and delete the VM; delete the snapshot.
6. Optionally plan this with vm_agentic_workflow action=sandbox_workflow first.

## 14. Tutorial 11 - Plan a VM Config with the Agent

Goal: get a sensible VM configuration for a use case.

1. Call vm_agentic_workflow with action=suggest_config and a use_case (CI runner, malware
   sandbox, dev environment).
2. Review the suggested os_type, memory, disk, and network.
3. Create the VM with those values.
4. Adjust if the host cannot meet them.

## 15. Tutorial 12 - Manage a Proxmox Cluster

Goal: manage VMs on a remote Proxmox host.

1. Ensure PROXMOX_HOST, PROXMOX_USER, and PROXMOX_PASSWORD are set.
2. Call proxmox_management action=list_vms.
3. Start/stop/shutdown VMs with the corresponding actions.
4. Create, list, and delete snapshots.
5. Check node_status and cluster_resources.

## 16. Tutorial 13 - Capture a VM Screenshot

Goal: visually verify a VM.

1. Start the VM.
2. Call system_management action=screenshot with the vm_name.
3. Review the captured image.
4. Use this to confirm a boot or a GUI state.

## 17. Tutorial 14 - Discover the Tool Surface

Goal: learn what the server can do.

1. Call info_tools action=list_tools with no filter to see everything.
2. Filter by category (vm, network, snapshot, storage, system, discovery, hyperv) and search.
3. Call action=help for usage.
4. Use action=tool_info for a specific tool.

## 18. REST and Webapp Notes

The server can run over HTTP (MCP_TRANSPORT=http or --transport http) on the MCP port, with
CORS and an optional API_KEY. The webapp frontend runs on 10700 and the REST backend on 10701.
For pure agent use, stdio mode needs no webapp.

## 19. Troubleshooting

- VBoxManage not found: set VBOX_MANAGE_PATH or install VirtualBox.
- create fails with ResourceQuotaExceededError: the host lacks memory. Free RAM or lower
  memory_mb; do not bypass the guard.
- start fails: confirm os_type is valid and a disk is attached; use ostypes and
  list_controllers.
- Hyper-V unavailable: your Windows edition or feature is missing; use VirtualBox.
- Proxmox returns not-configured: set PROXMOX_HOST and credentials.
- Sandbox times out: raise the timeout or simplify the code; check network_enabled.
- libvirt not on Windows: it is Linux/WSL2 only.
- Snapshot restore fails: the VM must be stopped or the hypervisor must support live restore;
  stop the VM first.

## 20. FAQ

- Which hypervisor is used? VirtualBox by default; Hyper-V on Windows, libvirt on
  Linux/WSL2, Proxmox when configured.
- Can it create a VM? Yes, vm_management create.
- Can it snapshot? Yes, snapshot_management.
- Can it run code? Yes, sandbox_management.
- Does it need a GPU? No.
- Is it safe for risky work? Yes, use the snapshot/restore pattern.
- Does it manage VMware/OpenStack? No.
- Can I use it over the network? Yes, HTTP transport.
- How do I get many isolated environments? Clone a base VM.

## 21. Best Practices

- Discover before acting: info_tools list_tools and system_management ostypes first.
- Snapshot before destructive work; clean up snapshots after.
- Prefer headless start for unattended work.
- Use clones for repeatable environments.
- Use sandboxes for throwaway or untrusted code.
- Respect ResourceGuard; free memory rather than bypassing it.
- Destroy sandboxes, terminate Windows Sandbox, and delete clones when done.
- Keep hypervisor credentials in environment configuration, not source control.

## 22. Quick Operation Reference

- vm_management: list, create, start, stop, delete, clone, reset, pause, resume, info.
- snapshot_management: list, create, restore, delete.
- network_management: list_networks, create_network, remove_network, list_adapters,
  configure_adapter.
- storage_management: list_controllers, create_controller, remove_controller, list_disks,
  create_disk, attach_disk.
- system_management: host_info, vbox_version, ostypes, metrics, screenshot.
- sandbox_management: execute_code, execute_file, session_*, win_sandbox_*.
- info_tools: list_tools, tool_info, tool_schema, help.
- hyperv_management: list, get, start, stop.
- libvirt_management: list, start, stop, status.
- proxmox_management: list_vms, start_vm, stop_vm, shutdown_vm, status, snapshots, node
  status, cluster resources.
- vm_agentic_workflow: suggest_config, sandbox_workflow, workflow.
- Prefab: show_vm_card, show_hypervisor_health_card, show_sandbox_status_card.

## 23. More Scenarios

Scenario A, disposable test: create a minimal VM, run the test headless, stop and delete it.

Scenario B, CI runner: create a VM with a CI-capable os_type, configure NAT, snapshot before
each job, restore on failure, tear down.

Scenario C, isolated code: use execute_code for a quick script, or a session for stateful
code; destroy the session after.

Scenario D, template library: provision a base, snapshot a clean state, and clone from it for
each task.

Scenario E, Windows tooling: launch a devinfra Windows Sandbox for Windows-specific work, then
terminate it.

## 24. Final Notes

Virtualization MCP abstracts many hypervisors behind one interface, so an agent can manage
VirtualBox and Hyper-V VMs, run Docker and Windows Sandbox sessions, and reach Proxmox
remotely without learning each hypervisor's CLI. Use the snapshot/restore pattern for safety,
sandboxes for isolation, and clones for repeatability. When in doubt, discover the surface
with info_tools and check host capacity before provisioning.

## 25. Deep Dive: vm_management

The vm_management tool is the primary VM lifecycle surface.

- list: returns VMs and their power state; use limit and offset for paging.
- create: requires a valid os_type. memory_mb defaults to 2048, disk_size_gb to 20. After
  create you must attach a disk and configure a network before a reliable start.
- start: defaults to headless. A VM that fails to start usually lacks an attached disk or has
  an invalid os_type.
- stop: powers the VM down; use reset for a hard reboot, pause/resume for suspend.
- clone: copies a source VM into a new VM; the cheapest path to many isolated environments.
- delete: removes a VM; destroy any snapshots first.
- info: detailed state for one VM.

## 26. Deep Dive: snapshot_management

Snapshots are the core safety mechanism.

- create: snapshot_name plus an optional description. Name it meaningfully (pre-work-clean).
- list: shows the snapshot tree for a VM.
- restore: rolls a VM back to a saved snapshot. The VM may need to be stopped first,
  depending on the hypervisor.
- delete: removes a snapshot; this is not undoable, so only delete when the snapshot is
  obsolete.

Always snapshot before a destructive or risky operation. Snapshots consume disk, so remove
them when you no longer need them.

## 27. Deep Dive: network_management

- list_networks: shows host-only networks.
- create_network: creates a host-only network with a name, ip, and netmask.
- remove_network: deletes a host-only network.
- list_adapters: shows a VM's network adapters.
- configure_adapter: changes an adapter. adapter_slot selects the adapter (0-3); network_type
  is nat, bridged, hostonly, internal, generic, or natnetwork.

Use NAT for general internet access, host-only for an isolated test network among VMs, and
bridged when a VM should appear directly on the LAN.

## 28. Deep Dive: storage_management

- list_controllers: shows a VM's storage controllers.
- create_controller: adds a controller of type ide, sata, scsi, sas, usb, or pcie.
- remove_controller: removes a controller.
- list_disks: shows virtual disks.
- create_disk: creates a VDI/Standard disk of a given size.
- attach_disk: attaches a disk to a VM, typically on SATA port 0.

A fresh VM needs at least one attached disk to boot an OS.

## 29. Deep Dive: sandbox_management

- execute_code: throwaway execution of code in a language (python, javascript, bash) with a
  timeout and optional network. Ephemeral; no cleanup.
- execute_file: execute a file from the host.
- session_create: create a persistent session (default image python:3.13-slim).
- session_run: run a command in a session.
- session_write_file / session_read_file: exchange files with a session.
- session_list / session_destroy: manage session lifecycle.
- win_sandbox_launch_consumer / win_sandbox_launch_devinfra: launch Windows Sandbox
  instances.
- win_sandbox_status / win_sandbox_terminate: control them.

Choose execute_code for one-offs and sessions for stateful work.

## 30. Deep Dive: vm_agentic_workflow

- suggest_config: given a use case, suggests os_type, memory, disk, and network.
- sandbox_workflow: plans a spin-up, work, snapshot, tear-down sequence for a goal.
- workflow: orchestrates a multi-step VM goal.

These use sampling and need a sampling-capable client; they fall back to sensible defaults
when sampling is unavailable.

## 31. Deployment Scenarios

- Local workstation: VirtualBox, default config, stdio transport for Claude Desktop.
- CI host: headless VMs, NAT networking, snapshot before each job.
- Team test cluster: clones on a host-only network, managed over HTTP with API_KEY.
- Remote cluster: Proxmox with PROXMOX_HOST set, managed over REST.
- Secure untrusted code: isolated VM or Docker sandbox, off the LAN.

## 32. Performance Guidance

- Host RAM is the main constraint; honor ResourceGuard.
- Use headless start and keep VMs minimal for many concurrent machines.
- Use clones rather than full provisioning for repeatable environments.
- Destroy sandboxes and delete snapshots to reclaim disk.
- Check system_management metrics before large provisioning runs.

## 33. Security Guidance

- Respect ResourceGuard and do not bypass memory limits.
- Snapshot before destructive operations.
- Keep untrusted code in an isolated VM or sandbox off the LAN.
- Restrict HTTP exposure with CORS_ORIGINS and API_KEY.
- Keep Proxmox credentials in environment configuration.
- Clean up experimental resources.

## 34. Glossary

- VM: a virtual machine; an isolated guest OS on a hypervisor.
- Guest / host: the OS inside the VM / the physical machine running it.
- Hypervisor: VirtualBox, Hyper-V, libvirt/KVM, Proxmox.
- Snapshot: a saved VM state for rollback.
- Clone: a full VM copy used as a template.
- NAT / host-only / bridged: network modes.
- Adapter slot: a VM network adapter index (0-3).
- VDI: the VirtualBox disk format.
- Headless: running a VM without a GUI.
- Sandbox: a disposable isolated execution environment.
- WSL2: Windows Subsystem for Linux 2, where libvirt/KVM runs.

## 35. Extended Scenario: Distro Testing

1. Create a VM with a candidate distro's os_type.
2. Snapshot the clean install.
3. Run package updates and tests.
4. Restore to the clean snapshot to repeat, or delete the VM when done.

## 36. Extended Scenario: Database Sandbox

1. Create a VM with a database-capable os_type and adequate memory.
2. Install and configure the database inside the VM.
3. Snapshot a clean configured state.
4. Clone the snapshot for each test environment.
5. Tear down when finished.

## 37. Extended Scenario: Network Lab

1. Create a host-only network.
2. Create several VMs and attach them to that network with configure_adapter.
3. Start them headless.
4. Run network experiments in isolation from the LAN.
5. Remove the network and VMs when done.

## 38. More FAQ

- What happens if I create without an os_type? The server rejects it; os_type is required.
- Can I change a VM's memory after create? It depends on the hypervisor; generally you must
  stop the VM and reconfigure.
- Do snapshots work on Hyper-V? No; Hyper-V has no PowerShell snapshot API in this server.
- Can I run Windows in a sandbox? Yes, via Windows Sandbox on Windows Pro/Enterprise.
- How do I get more disk? Create and attach additional disks.
- Is there a web dashboard? Yes, frontend on 10700, backend on 10701.
- Can multiple agents share the server? Yes, over HTTP with a shared API key.

## 39. Getting Help

- info_tools action=list_tools and action=help for the surface and usage.
- system_management action=ostypes and host_info for environment facts.
- show_vm_card, show_hypervisor_health_card, and show_sandbox_status_card for status.
- system_management action=screenshot for visual verification.
- The README and docs in the repo for full details.

## 40. Best Practices Summary

Discover before you act, snapshot before risky work, prefer clones for repeatability, sandbox
untrusted code, respect resource limits, and clean up when you are done. Virtualization MCP
makes VM and sandbox management scriptable and safe across many backends with one interface.

## 41. Working with Hyper-V

Hyper-V management is Windows-only and covers lifecycle: list, get, start, and stop, with
force and wait options. Hyper-V has no PowerShell snapshot API in this server, so use
VirtualBox for snapshot-heavy workflows. On unsupported editions (for example Windows Home)
the server degrades gracefully and reports that Hyper-V is unavailable rather than failing
hard.

## 42. Working with libvirt/KVM

libvirt management runs on Linux and WSL2 and covers list, start, stop, and status via virsh.
It is the natural backend on Linux hosts. Ensure libvirt and the virsh client are installed
and the libvirt daemon is running before use.

## 43. Working with Proxmox

Proxmox management activates only when PROXMOX_HOST is set, along with PROXMOX_USER and
PROXMOX_PASSWORD. It covers list_vms, start_vm, stop_vm, shutdown_vm, status, snapshots, node
status, and cluster resources, all over the Proxmox REST API. If the host is not configured,
the tool returns a clear not-configured message.

## 44. Working with Windows Sandbox

Windows Sandbox provides ephemeral Windows environments on Windows Pro and Enterprise. Launch
a devinfra or consumer sandbox, check its status, and terminate it when done. Use it for
Windows-specific tooling that Docker and Linux VMs cannot provide.

## 45. Choosing a Hypervisor

- Most general work: VirtualBox (full feature surface, cross-platform).
- Windows-native lifecycle: Hyper-V.
- Linux host: libvirt/KVM.
- Remote cluster: Proxmox.
- Throwaway code: Docker sandbox or Windows Sandbox.

Pick the backend that fits the platform and the workload; the server exposes a uniform
interface regardless.

## 46. Resource Planning

- Each VM reserves memory and disk. Plan for the total across all VMs, not per VM.
- ResourceGuard refuses to create or start a VM that would push the host above 95% memory or
  exceed available RAM.
- Snapshots and clones consume disk; budget for them.
- Prefer headless and minimal VMs for many concurrent instances.
- Check system_management metrics before large provisioning runs.

## 47. Automating with the Agent

- Use vm_agentic_workflow to plan configs and sandboxed workflows.
- Call info_tools to discover the exact surface before scripting.
- Snapshot before every destructive automation step.
- Use clones for parallel, isolated tasks.
- Tear down and clean up in the same automation that created the resources.

## 48. Common Pitfalls

- Creating without a valid os_type: the server rejects it; check ostypes.
- Forgetting to attach a disk before start: the VM will not boot.
- Leaving snapshots around: they consume disk.
- Oversubscribing host memory: ResourceGuard blocks it.
- Running untrusted code on a bridged VM: prefer an isolated or off-LAN environment.
- Trying to use Hyper-V snapshots: not supported in this server.

## 49. Troubleshooting Expansion

- VM stuck in a state: use reset for a hard reboot, or stop then start.
- Snapshot restore fails: stop the VM first, then restore.
- Sandbox session lost: use session_list; if it is gone, create a new session.
- Proxmox auth fails: check PROXMOX_HOST, PROXMOX_USER, and PROXMOX_PASSWORD.
- libvirt daemon down: start the libvirt service.
- Windows Sandbox fails: confirm Windows Pro/Enterprise and that the feature is enabled.

## 50. Deployment Checklist

- Install a hypervisor and set its path variable.
- Install the server with uv.
- Configure environment (defaults, Proxmox, transport, timeouts).
- Run the server (stdio for Claude, http for remote).
- Verify with system_management and info_tools.
- Register in the MCP host config.
- Snapshot before first risky operation.

## 51. Prompts That Work Well

- "List my VMs and their state."
- "Create a disposable Ubuntu VM with 4GB RAM and snapshot it."
- "Clone my base VM for a new test."
- "Run this Python snippet in a sandbox."
- "Launch a Windows Sandbox for a dev environment."
- "Set up a host-only network for three test VMs."
- "Roll the VM back to the pre-work snapshot."
- "Plan a safe sandboxed workflow to test an untrusted package."

## 52. Final Guidance

Virtualization MCP gives you one scriptable interface over VMs, snapshots, networking,
storage, and sandboxes across VirtualBox, Hyper-V, libvirt/KVM, Proxmox, Docker, and Windows
Sandbox. Lead with discovery, protect with snapshots, isolate with sandboxes, and scale with
clones. Clean up what you create, and the host stays healthy and predictable.

## 53. Storage Layout and Disk Management

Understand how disks and controllers relate before attaching storage.

- A VM needs at least one storage controller (ide, sata, scsi, sas, usb, pcie). SATA is the
  common default.
- Disks are virtual files (VDI/Standard by default). create_disk allocates the file; attach
  it to a controller on a VM.
- list_controllers tells you which controller to attach to; list_disks shows existing disks.
- To grow capacity, create and attach additional disks rather than resizing in place.
- Snapshot a clean state before changing storage so you can roll back.

## 54. Networking Modes Explained

- NAT: the default; the guest shares the host's network through address translation. Good
  for general internet access from the guest.
- Bridged: the guest gets its own address on the physical LAN. Use when the guest must be
  reachable on the network.
- Host-only: a private network between host and guests, isolated from the LAN. Best for
  multi-VM test labs and untrusted code.
- Internal: isolated from the host too; only guests on the same internal network can talk.
- Generic/NAT network: advanced modes for special setups.

Choose the mode that matches your isolation and reachability requirements, and use
configure_adapter with the right adapter_slot.

## 55. Snapshot Hygiene

- Snapshot before destructive or risky operations, not after.
- Name snapshots meaningfully so you can tell them apart (pre-upgrade, pre-clean).
- Restore to roll back; delete snapshots once they are obsolete.
- A deep snapshot tree slows the VM and consumes disk; keep it shallow.
- For a repeatable baseline, keep one clean snapshot and clone from it.

## 56. When to Snapshot vs Clone vs Sandbox

- Snapshot: you need to roll back the same VM to a prior state.
- Clone: you need many independent copies of one setup.
- Sandbox: you need throwaway code execution or an ephemeral OS with no persistence.

Choose the mechanism that matches the goal; they are not interchangeable.

## 57. Working with Headless VMs

- start defaults to headless, which is ideal for unattended, CI, or server workloads.
- You can still take screenshots with system_management screenshot for visual verification.
- Headless VMs consume fewer host resources than GUI VMs.
- For a GUI session, start the VM through the hypervisor's own console if needed.

## 58. Backup and Recovery Guidance

- Use snapshots as the primary rollback mechanism for short-lived risk.
- For longer-lived data, back up the VM disk files or use a hypervisor export (OVA/OVF).
- Keep a clean baseline snapshot and clone from it for recovery.
- Verify a restore works by actually restoring to a snapshot in a test VM.

## 59. Multi-Host and Remote Operation

- Proxmox extends management to a remote cluster over REST.
- HTTP transport lets remote clients drive the server with CORS and API_KEY.
- Keep hypervisor credentials and API keys in environment configuration.
- Restrict exposure to trusted hosts when the server is reachable over a network.
