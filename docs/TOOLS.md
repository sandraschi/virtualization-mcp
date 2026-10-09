# virtualization-mcp — Tool Reference

Portmanteau tools (one tool per domain, `action`/`operation` selects the op).
Full parameter schemas: call `info_tools(action="tool_schema", tool_name="<name>")`.

| Tool | Actions |
|------|---------|
| `vm_management` | list, create, start, stop, delete, clone, reset, pause, resume, info |
| `network_management` | list_networks, create_network, remove_network, list_adapters, configure_adapter |
| `snapshot_management` | list, create, restore, delete |
| `storage_management` | list_controllers, create_controller, remove_controller, list_disks, create_disk, attach_disk |
| `system_management` | host_info, vbox_version, ostypes, metrics, screenshot |
| `sandbox_management` | execute_code, execute_file, session_create/run/write_file/read_file/list/destroy, win_sandbox_launch_consumer/devinfra/status/terminate, win_sandbox_naked_test/status/list |
| `hyperv_management` | list, get, start, stop (Windows only) |
| `libvirt_management` | list, start, stop, status (Linux/WSL2) |
| `proxmox_management` | list_vms, start_vm, stop_vm, shutdown_vm, status, create_snapshot, list_snapshots, delete_snapshot, node_status, cluster_resources |
| `discovery_management` | list_tools, tool_info, tool_schema, help (as `info_tools`) |
| `vm_agentic_workflow` | suggest_config, sandbox_workflow, workflow (LLM sampling) |
| `show_vm_card`, `show_hypervisor_health_card`, `show_sandbox_status_card` | Prefab UI cards |

All tools return `{"success": bool, ...}` with human-readable `error` on failure.
See `llms-full.txt` for the full reference and `docs/CONFIGURATION.md` for env vars.
