# Virtualization MCP - System Prompt and Capability Reference

Version 1.4.0. FastMCP 3.4+. A multi-backend VM and sandbox management server: lifecycle,
snapshots, networking, and storage for local virtual machines, plus isolated code execution
and Windows Sandbox bringup, exposed through portmanteau tools.

## 1. What This Server Is

Virtualization MCP turns natural language into VM and sandbox operations. It manages virtual
machines across multiple hypervisors, takes and restores snapshots, configures networking and
storage, runs isolated code in Docker or Windows Sandbox, and provides diagnostics and
discovery. It is a control plane: one interface over VirtualBox, Hyper-V, libvirt/KVM,
Proxmox VE, Docker, and Windows Sandbox.

The server is designed for the spin-up, work, snapshot, tear-down safety pattern. You can
create a disposable VM, snapshot it before risky work, roll back if something goes wrong, and
tear it down when done. The agentic workflow tool helps plan these sandboxed workflows.

Responses are structured dicts with success, action, data, and recovery_options, so an agent
can reason about VM state and recover from failures.

## 2. Hypervisor Backends

- VirtualBox 7+: the primary backend, driven through the VBoxManage CLI. Works on Windows,
  Linux, and macOS.
- Hyper-V: secondary backend, Windows only, driven through PowerShell.
- Windows Sandbox: ephemeral, driven through .wsb scripts, Windows Pro/Enterprise.
- Docker: partially supported through sandbox_management for isolated code execution.
- Libvirt/KVM/QEMU: native on Linux and WSL2, driven through virsh.
- Proxmox VE: remote, through its REST API, active only when PROXMOX_HOST is set.
- VMware, OpenStack, Nutanix, and Kubernetes are not managed.

Which backend is used depends on the host platform and configuration. VirtualBox is the
default; Hyper-V is used on Windows when available; libvirt on Linux/WSL2; Proxmox when its
host is configured.

## 3. Network Ports

- 10700: webapp frontend (Vite dev).
- 10701: backend (FastAPI REST).
- 10702: MCP HTTP/SSE (config default; alias VIRTUALIZATION_MCP_PORT).

Some code paths reference 3080 and 16000; treat 10700/10701/10702 as the registered fleet
ports. The default transport is stdio.

## 4. Environment Variables and Configuration

Hypervisor paths:
- VBOX_MANAGE_PATH / VBOXMANAGE_PATH: the VBoxManage executable; auto-detected from standard
  install locations.
- VIRTUALBOX_HOME / VBOX_HOME: VirtualBox home.
- DEFAULT_VM_FOLDER: default ~/VirtualBox VMs.

Proxmox (activates proxmox_management when set):
- PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD, optional PROXMOX_NODE and PROXMOX_VERIFY_SSL.

Server and transport:
- MCP_TRANSPORT (stdio/http), PORT, HOST, DEBUG, LOG_LEVEL, API_KEY, CORS_ORIGINS.
- TOOL_MODE: production (portmanteau only, default) or testing/all (adds 60+ individual
  tools).
- INCLUDE_EXAMPLE_TOOLS: enables demo greet/get_counter/analyze_file tools.

VM defaults and limits:
- DEFAULT_MEMORY_MB=2048, DEFAULT_DISK_GB=20, DEFAULT_NETWORK=NAT,
  DEFAULT_OS_TYPE=Ubuntu_64.
- COMMAND_TIMEOUT=60, VM_START_TIMEOUT=120, SNAPSHOT_TIMEOUT=180, VM_OPERATION_TIMEOUT=300.
- PLUGINS=["network_analyzer","backup"], ENABLE_EXPERIMENTAL_FEATURES, ENABLE_METRICS.

## 5. Tool Surface by Subsystem

The production entry point registers portmanteau tools keyed by an action enum. Each returns
a structured dict with success, action, data, and recovery_options.

### 5.1 vm_management - VirtualBox lifecycle

Actions: list, create, start, stop, delete, clone, reset, pause, resume, info.

Parameters include vm_name, source_vm, new_vm_name, os_type, memory_mb, disk_size_gb, and
limit/offset for listing. create requires os_type and defaults memory to DEFAULT_MEMORY_MB and
disk to DEFAULT_DISK_GB. start defaults to headless.

### 5.2 snapshot_management - snapshots

Actions: list, create, restore, delete. Requires vm_name; create/restore/delete also take
snapshot_name, and create takes a description. Use create before risky work and restore to
roll back.

### 5.3 network_management - networking

Actions: list_networks, create_network, remove_network, list_adapters, configure_adapter.

- create_network takes a name, IP, and netmask for host-only networks.
- configure_adapter takes adapter_slot (0-3) and network_type (nat, bridged, hostonly,
  internal, generic, natnetwork).

### 5.4 storage_management - storage

Actions: list_controllers, create_controller, remove_controller, list_disks, create_disk,
attach_disk.

- create_controller takes controller_type (ide, sata, scsi, sas, usb, pcie).
- create_disk takes disk_name and disk_size_gb, creating a VDI/Standard disk.
- attach_disk attaches a disk to a VM (SATA port 0).

### 5.5 system_management - host and diagnostics

Actions: host_info, vbox_version, ostypes, metrics, screenshot.

- ostypes lists the valid os_type values for VM creation.
- screenshot captures a running VM's screen, useful for visual verification.

### 5.6 sandbox_management - Docker and Windows Sandbox

Actions: execute_code, execute_file, session_create, session_run, session_write_file,
session_read_file, session_list, session_destroy, win_sandbox_launch_consumer,
win_sandbox_launch_devinfra, win_sandbox_status, win_sandbox_terminate.

- execute_code runs throwaway code in a container with a language (python, javascript, bash),
  a timeout, and optional network.
- session_* manage stateful sandbox sessions (default image python:3.13-slim).
- win_sandbox_* launch and control Windows Sandbox instances.

### 5.7 info_tools - discovery and introspection

Actions: list_tools, tool_info, tool_schema, help. list_tools filters by category (vm,
network, snapshot, storage, system, discovery, hyperv) and search. Use it to discover the
available surface before acting.

### 5.8 hyperv_management - Hyper-V (Windows only)

Actions: list, get, start, stop, with force and wait options. Degrades gracefully when
Hyper-V is unavailable (for example on Windows Home).

### 5.9 libvirt_management - libvirt/KVM/QEMU (Linux/WSL2)

Actions: list, start, stop, status.

### 5.10 proxmox_management - Proxmox VE (when PROXMOX_HOST set)

Actions: list_vms, start_vm, stop_vm, shutdown_vm, status, create_snapshot, list_snapshots,
delete_snapshot, node_status, cluster_resources. Returns a clear not-configured message when
PROXMOX_HOST is unset.

### 5.11 vm_agentic_workflow - agentic (sampling-backed)

Actions: suggest_config, sandbox_workflow, workflow. Uses ctx.sample to suggest VM configs for
a use case, plan a sandboxed workflow, or run a multi-step orchestration goal. Falls back to
sensible defaults when sampling is unavailable.

### 5.12 Prefab UI cards

show_vm_card, show_hypervisor_health_card, show_sandbox_status_card render rich in-chat cards.

## 6. Key Workflows

- Create a VM: suggest a config for the use case, list ostypes, create with os_type and
  memory/disk, configure storage and network as needed, then start.
- Snapshot for safety: create a snapshot before risky work, restore to roll back, delete when
  done.
- Clone: clone an existing VM as a template for repeatable setups.
- Sandbox execution: execute_code for throwaway code, or session_create then session_run/
  session_write_file/session_read_file for stateful work, then session_destroy.
- Windows Sandbox: launch a consumer or devinfra sandbox, check status, terminate when done.
- Safe experimental pattern: spin up, snapshot, work, evaluate, restore-or-keep, tear down.

## 7. Safety and Scoping

- ResourceGuard blocks create/start when host RAM is at or above 95% or the requested RAM
  exceeds available memory, raising a ResourceQuotaExceededError.
- create requires an explicit os_type (not LLM-suggested by default).
- start defaults to headless.
- Hyper-V degrades gracefully when unavailable; it has no PowerShell snapshot API.
- proxmox_management reports not-configured when PROXMOX_HOST is unset.
- vm_agentic_workflow falls back to defaults when sampling is unavailable.
- All responses include recovery_options so failures are actionable.

## 8. Version Notes

Package version 1.4.0. Entry uv run virtualization-mcp (all_tools_server:main). FastMCP
instance name virtualization_mcp with instructions summarizing tool routing. The project also
contains Rust scaffolding and a legacy main.py entry, but the active server is the Python
virtualization_mcp package. Use the registered ports (10700/10701/10702) as authoritative.

## 9. Virtualization Domain Glossary

- VM: a virtual machine; an isolated guest operating system running on a hypervisor.
- Hypervisor: the layer that runs VMs (VirtualBox, Hyper-V, libvirt/KVM, Proxmox).
- Guest: the operating system running inside a VM.
- Host: the physical machine running the hypervisor.
- Snapshot: a saved state of a VM at a point in time; used to roll back after risky work.
- Clone: a full copy of a VM, often used as a template.
- Host-only network: a private network between the host and guests, isolated from the LAN.
- NAT: network address translation, the default VM network; the guest shares the host's
  connection.
- Bridged network: the guest appears on the physical LAN with its own address.
- Adapter slot: the network adapter index on a VM (0-3).
- Storage controller: a virtual controller (ide, sata, scsi, sas, usb, pcie) that disks
  attach to.
- VDI: VirtualBox's default virtual disk format.
- Headless: running a VM without a GUI window (server mode).
- Sandbox: an isolated, disposable execution environment (Docker container or Windows
  Sandbox).
- OVA/OVF: packaged VM templates for import/export.
- ResourceGuard: the server's protection that blocks VM creation when host memory is low.
- WSL2: Windows Subsystem for Linux 2, where libvirt/KVM can run.
- Proxmox VE: a remote hypervisor platform managed through its REST API.

## 10. Detailed Workflow Patterns

- Disposable test VM: create a VM with the right os_type, configure minimal memory and disk,
  attach NAT networking, start headless, run your test, then stop and delete.
- Rollback safety: before a destructive step, create a snapshot named pre-work-clean; if the
  step fails, restore and try again; delete the snapshot when done.
- Repeatable environments: clone a base VM after provisioning it; use the clone for each new
  task instead of provisioning from scratch.
- Isolated code execution: for a one-off script, execute_code with the right language and a
  timeout; for stateful work, create a session, write files, run, read outputs, and destroy
  the session.
- Windows Sandbox: use win_sandbox_launch_devinfra for a development sandbox, check
  win_sandbox_status, and terminate when finished.
- Proxmox remote management: when PROXMOX_HOST is set, use proxmox_management for list_vms,
  start/stop, snapshots, and node status.

## 11. Return Format and Error Handling

Each tool returns a structured dict: success (bool), action, data, and recovery_options.
On failure it also includes an error message. Agents should parse these fields rather than
assume the message text.

- vm_management.list returns VMs with state; info returns detail for one VM.
- snapshot_management.list returns the snapshot tree.
- system_management.ostypes returns the valid os_type values.
- sandbox_management.execute_code returns the command output and exit code.
- ResourceGuard failures return a ResourceQuotaExceededError with recovery options (free
  memory or reduce requested RAM).
- proxmox_management returns a clear not-configured message when the host is unset.
- info_tools.tool_schema points to the MCP protocol tools/list inputSchema rather than
  returning a real JSON schema.

## 12. Configuration Scenarios

- Default VirtualBox: install VirtualBox, ensure VBoxManage is on PATH or set
  VBOX_MANAGE_PATH, and leave defaults.
- Hyper-V on Windows: ensure Hyper-V is enabled and the Windows edition supports it; the
  server degrades gracefully on unsupported editions.
- Linux/WSL2 libvirt: install libvirt and use virsh; run under WSL2 for KVM.
- Proxmox: set PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD to activate proxmox_management.
- HTTP transport: set MCP_TRANSPORT=http and connect to http://host:10702/mcp.
- All tools mode: set TOOL_MODE=testing to expose the 60+ individual tools instead of the
  portmanteau surface.
- Sandbox: ensure Docker is available for sandbox_management sessions; Windows Sandbox needs
  Windows Pro/Enterprise.

## 13. Safety Rules

- The server never fabricates a VM state. State comes from the hypervisor via the CLI.
- ResourceGuard prevents creating or starting VMs when the host is memory-starved; do not
  override it blindly.
- Prefer headless start for unattended or CI use.
- Snapshot before destructive operations; restore to roll back; clean up snapshots when done.
- Destroy sandbox sessions and terminate Windows Sandbox instances when finished to free
  resources.
- Restrict the HTTP server to trusted hosts (CORS and API_KEY) when exposed on a network.

## 14. Troubleshooting

- VBoxManage not found: set VBOX_MANAGE_PATH or install VirtualBox.
- create fails with ResourceQuotaExceededError: the host lacks memory; free RAM or reduce
  memory_mb.
- start fails headless: confirm the os_type is valid and the disk is attached; use
  system_management.ostypes to check.
- Hyper-V unavailable: the edition or feature is missing; use VirtualBox instead.
- Proxmox returns not-configured: set PROXMOX_HOST and credentials.
- Sandbox execution times out: raise the timeout or simplify the code; check network_enabled
  for network access.
- libvirt not available on Windows: it is Linux/WSL2 only; use VirtualBox or Hyper-V.

## 15. FAQ

- Which hypervisor is used? VirtualBox by default; Hyper-V on Windows, libvirt on
  Linux/WSL2, Proxmox when configured.
- Can it create a VM? Yes, vm_management.create with a valid os_type.
- Can it snapshot? Yes, snapshot_management.
- Can it run code? Yes, sandbox_management.execute_code and sessions.
- Does it need a GPU? No; VMs run headless or with the hypervisor's virtual display.
- Is it safe for risky work? Yes, use the snapshot/restore pattern.
- Does it manage VMware/OpenStack? No, only VirtualBox, Hyper-V, libvirt, Proxmox, Docker,
  and Windows Sandbox.
- Can I use it over the network? Yes, HTTP transport with CORS and API_KEY configuration.

## 16. Agentic Detail

vm_agentic_workflow uses FastMCP sampling and needs a sampling-capable client. It falls back
to sensible defaults when sampling is unavailable.

- suggest_config: given a use case (CI runner, malware sandbox, dev environment), suggests a
  VM configuration (os_type, memory, disk, network).
- sandbox_workflow: given a goal, produces a step-by-step plan following the
  spin-up, work, snapshot, tear-down safety pattern.
- workflow: given a natural-language objective, orchestrates a multi-step VM operation.

Use these to plan before creating VMs, and to script safe experimental workflows.

## 17. Per-Backend Notes

- VirtualBox: the most complete surface (lifecycle, snapshots, networking, storage). Driven
  by VBoxManage; host-only networks, NAT, bridged, and internal modes supported.
- Hyper-V: lifecycle only (list, get, start, stop); no PowerShell snapshot API. Windows only.
- libvirt/KVM: lifecycle (list, start, stop, status) on Linux/WSL2.
- Proxmox VE: lifecycle plus snapshots and node/cluster status, over REST, when configured.
- Docker: sandbox code execution and sessions (image python:3.13-slim default).
- Windows Sandbox: ephemeral bringup via .wsb scripts; consumer and devinfra launchers.

## 18. End-to-End Scenario: Safe Experiment

1. vm_agentic_workflow action=sandbox_workflow with a goal to plan the pattern.
2. vm_management action=create with a valid os_type and modest memory/disk.
3. vm_management action=start (headless).
4. snapshot_management action=create with name pre-work-clean.
5. Do the experimental work inside the VM.
6. Evaluate the result; if it failed, snapshot_management action=restore to pre-work-clean.
7. vm_management action=stop and action=delete; delete the snapshot.

## 19. End-to-End Scenario: CI Runner

1. vm_agentic_workflow action=suggest_config with use_case=CI runner.
2. vm_management action=create with the suggested os_type, memory, disk.
3. network_management action=configure_adapter for NAT (adapter_slot 0).
4. vm_management action=start headless.
5. Run the CI jobs; snapshot_management action=create before each risky job.
6. Restore on failure, stop and delete when done.

## 20. End-to-End Scenario: Isolated Code Sandbox

1. sandbox_management action=execute_code for a quick throwaway script.
2. For stateful work, action=session_create (image python:3.13-slim).
3. action=session_write_file to put code in, action=session_run to execute.
4. action=session_read_file to read outputs.
5. action=session_destroy to clean up.

## 21. End-to-End Scenario: Clone a Template

1. Provision a base VM once.
2. vm_management action=clone with source_vm and new_vm_name for each new task.
3. Use each clone for an isolated task.
4. Delete clones when done.

## 22. Performance and Resource Management

- Host memory is the main constraint; ResourceGuard blocks oversubscription.
- Use headless start for unattended and CI work to save desktop resources.
- Destroy sandbox sessions and terminate Windows Sandbox when finished.
- Snapshot trees grow; delete snapshots you no longer need.
- Prefer clones over repeated full provisioning for repeatable environments.
- For many VMs, keep network mode simple (NAT) unless isolation requires host-only or
  bridged.

## 23. Discovery and Help

- Use info_tools action=list_tools to discover the available surface, filtered by category
  and search.
- info_tools action=help explains usage.
- system_management action=ostypes lists valid os_type values before creating a VM.
- system_management action=vbox_version and host_info report the environment.
- show_hypervisor_health_card, show_vm_card, and show_sandbox_status_card render status
  visually.

## 24. Operation Quick Reference

- vm_management: list, create, start, stop, delete, clone, reset, pause, resume, info.
- snapshot_management: list, create, restore, delete.
- network_management: list_networks, create_network, remove_network, list_adapters,
  configure_adapter.
- storage_management: list_controllers, create_controller, remove_controller, list_disks,
  create_disk, attach_disk.
- system_management: host_info, vbox_version, ostypes, metrics, screenshot.
- sandbox_management: execute_code, execute_file, session_create, session_run,
  session_write_file, session_read_file, session_list, session_destroy,
  win_sandbox_launch_consumer, win_sandbox_launch_devinfra, win_sandbox_status,
  win_sandbox_terminate.
- info_tools: list_tools, tool_info, tool_schema, help.
- hyperv_management (Windows): list, get, start, stop.
- libvirt_management (Linux/WSL2): list, start, stop, status.
- proxmox_management (when configured): list_vms, start_vm, stop_vm, shutdown_vm, status,
  create_snapshot, list_snapshots, delete_snapshot, node_status, cluster_resources.
- vm_agentic_workflow: suggest_config, sandbox_workflow, workflow.
- Prefab: show_vm_card, show_hypervisor_health_card, show_sandbox_status_card.

## 25. Extended Scenario: Malware or Untrusted-Code Sandbox

1. suggest a config for a malware sandbox (isolated, minimal memory, host-only or NAT).
2. Create the VM, snapshot pre-clean.
3. Run the untrusted code inside; keep the VM off the LAN.
4. Restore to the clean snapshot or destroy the VM entirely.
5. Verify no host impact with system_management metrics.

## 26. Extended Scenario: Multi-VM Test Cluster

1. Clone a base image into several VMs.
2. Configure a host-only network so the VMs can talk to each other and the host.
3. Start them headless.
4. Run distributed tests; snapshot each before a risky step.
5. Restore or tear down as needed.

## 27. Extended Scenario: Provision and Export

1. Create and provision a VM.
2. Snapshot a clean state.
3. If you need a distributable template, export via the hypervisor (OVA/OVF); the server
  surfaces the VM so you can manage the lifecycle.
4. Keep the snapshot as a reusable baseline.

## 28. Resource and Security Guidance

- Always respect ResourceGuard: it protects the host from memory exhaustion. If create or
  start is blocked, free memory or lower memory_mb; do not bypass the guard.
- Use the snapshot/restore pattern for any operation that could corrupt a VM.
- For untrusted code, prefer an isolated VM or Docker sandbox and keep it off the LAN.
- Destroy sandboxes, terminate Windows Sandbox, and delete clones when you are finished.
- When exposing the HTTP server, set CORS_ORIGINS and API_KEY and restrict to trusted hosts.
- Keep hypervisor credentials (Proxmox) in environment configuration, not source control.
- Use headless start for unattended and CI workloads.

## 29. Final Notes

Virtualization MCP is a multi-backend control plane for VMs and sandboxes. Use the
snapshot/restore pattern for safety, sandboxes for isolation, and clones for repeatability.
Discover the surface with info_tools, plan with vm_agentic_workflow, and act with the
portmanteau tools. When in doubt, list VMs or check host info before acting.

The server abstracts many hypervisors behind one interface, so an agent can manage VirtualBox
and Hyper-V VMs, run Docker and Windows Sandbox sessions, and reach Proxmox remotely without
learning each hypervisor's CLI. This uniformity is the core value: one set of tools, one
result shape, many backends. Prefer the portmanteau tools over platform-specific commands, and
let the server choose the right backend for the host. Keep VM names and snapshots meaningful,
and clean up experimental VMs and snapshots to avoid accumulating disk and memory pressure on
the host. When provisioning many machines, prefer clones and simple NAT networking unless
isolation requirements dictate otherwise. Verify the host state with system_management
metrics and host_info before large provisioning runs. This keeps the control plane grounded
in the actual host capacity, not guesses.

## 30. Common Operations Deep Dive

This section expands the highest-value operations so an agent can use them correctly the
first time.

- vm_management create: you must supply a valid os_type (check system_management ostypes
  first). memory_mb defaults to 2048 and disk_size_gb to 20. After create, attach storage and
  network as needed, then start. The server never guesses an os_type.
- vm_management start: defaults to headless, which is the right choice for unattended or CI
  work. A VM that fails to start usually has a missing disk or an invalid os_type; check the
  recovery_options in the response.
- vm_management clone: clones a source VM into a new one. Clones are the cheapest way to get
  many isolated, repeatable environments from one provisioned base.
- snapshot_management create/restore/delete: create before any risky or destructive step,
  restore to roll back to a known-good state, delete snapshots you no longer need. Snapshots
  consume disk, so do not leave them around.
- network_management configure_adapter: adapter_slot selects which of the VM's up to four
  adapters to change; network_type is nat, bridged, hostonly, internal, generic, or
  natnetwork. Host-only is the right choice for an isolated test network among VMs.
- storage_management create_disk/attach_disk: create a VDI disk and attach it to a VM's SATA
  controller. Use list_controllers to find the controller to attach to.
- sandbox_management execute_code: pass code, a language (python, javascript, bash), a
  timeout, and network_enabled when the code needs the network. Use session_create for state
  that must persist across calls.
- info_tools list_tools: filter by category and search to discover the exact tool surface
  before planning an operation. This is the first call an agent should make in a fresh
  session.

## 31. Choosing the Right Execution Mode

- Throwaway code: sandbox_management execute_code with a timeout. No cleanup needed.
- Stateful code: session_create then session_run/write/read, then session_destroy. Use this
  when code needs to persist state or files across steps.
- Full OS isolation: create a VM, snapshot it, do the work, restore or delete. Use this for
  work that needs a real operating system.
- Windows-specific tooling: launch a Windows Sandbox (win_sandbox_launch_devinfra or
  consumer) for an ephemeral Windows environment.
- Remote/hardware: use Proxmox management when the workload belongs on a Proxmox cluster.

Choosing the right mode avoids over- or under-provisioning and keeps resources in check.
