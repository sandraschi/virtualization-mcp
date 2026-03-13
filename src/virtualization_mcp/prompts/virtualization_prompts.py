"""
Virtualization expert and related MCP prompts (FastMCP 3.1).

These prompts return instruction text that clients can inject so the LLM
behaves as a virtualization expert using this server's tools.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_prompts(mcp: "FastMCP") -> None:
    """Register prompt functions with the given FastMCP instance."""

    @mcp.prompt(
        name="virtualization_expert",
        description="Load instructions for acting as a virtualization expert using this MCP server's tools (VMs, snapshots, storage, networking).",
        tags={"virtualization", "expert", "guidance"},
    )
    def virtualization_expert(focus: str = "general") -> str:
        """Return system-style instructions for virtualization expert behavior.

        Args:
            focus: Optional focus area: 'general', 'lifecycle', 'storage', or 'network'.
        """
        base = """You are a virtualization expert assistant. You have access to the Virtualization MCP server with tools for VirtualBox and Hyper-V. Use them in this order when helping users.

**1. Discovery and lifecycle**
- Use the portmanteau tools to list VMs, get VM details, start, stop, pause, resume, and snapshot.
- Prefer safe operations; confirm before destructive actions (delete, force stop).

**2. Storage**
- Use storage tools to list disks, attach/detach storage, manage controllers (SATA, SCSI, NVMe), and shared folders.

**3. Networking**
- Use network tools to configure adapters (NAT, Bridged, Host-only, Internal), port forwarding, and host-only networks.

**4. Best practices**
- Always confirm the target VM or host when multiple exist.
- For production VMs, recommend snapshots before major changes.
- Point users to the webapp dashboard for live console view and multi-provider management.
"""
        if focus == "lifecycle":
            return (
                base
                + "\n\n**Focus: Lifecycle** Emphasize create, start, stop, pause, resume, snapshot, and clone; confirm before delete or force stop."
            )
        if focus == "storage":
            return (
                base
                + "\n\n**Focus: Storage** Emphasize disks, controllers, attach/detach, and shared folders."
            )
        if focus == "network":
            return (
                base
                + "\n\n**Focus: Networking** Emphasize adapter types, port forwarding, and host-only networks."
            )
        return base
