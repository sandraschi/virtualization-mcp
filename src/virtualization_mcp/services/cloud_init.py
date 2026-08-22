"""
Cloud-Init Seed ISO Generator for virtualization-mcp.

Generates bootable cloud-init user-data and meta-data ISO images for automated
non-interactive Linux VM provisioning (injecting SSH keys, hostname, users, and setup scripts).
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_cloud_init_config(
    hostname: str = "ubuntu-server",
    username: str = "ubuntu",
    ssh_public_key: str | None = None,
    password: str | None = None,
    run_commands: list[str] | None = None,
) -> tuple[str, str]:
    """Generate YAML string content for cloud-init `user-data` and `meta-data`.

    Args:
        hostname: Hostname for the VM instance.
        username: Default user account name.
        ssh_public_key: Optional SSH public key to embed in authorized_keys.
        password: Optional default user password.
        run_commands: Optional list of shell commands to run on first boot.

    Returns:
        Tuple of (user_data_yaml, meta_data_yaml).
    """
    meta_data = f"instance-id: {hostname}-init\nlocal-hostname: {hostname}\n"

    user_data_lines = [
        "#cloud-config",
        f"hostname: {hostname}",
        "manage_etc_hosts: true",
        "users:",
        f"  - name: {username}",
        "    sudo: ALL=(ALL) NOPASSWD:ALL",
        "    shell: /bin/bash",
    ]

    if password:
        user_data_lines.append(f"    plain_text_passwd: '{password}'")
        user_data_lines.append("    lock_passwd: false")

    if ssh_public_key:
        user_data_lines.append("    ssh_authorized_keys:")
        user_data_lines.append(f"      - {ssh_public_key}")

    if run_commands:
        user_data_lines.append("runcmd:")
        for cmd in run_commands:
            user_data_lines.append(f"  - {cmd}")

    return "\n".join(user_data_lines) + "\n", meta_data


def create_cloud_init_iso(
    output_iso_path: str,
    hostname: str = "ubuntu-server",
    username: str = "ubuntu",
    ssh_public_key: str | None = None,
    password: str | None = None,
    run_commands: list[str] | None = None,
) -> dict[str, Any]:
    """Create a cloud-init ISO seed file or configuration bundle.

    Args:
        output_iso_path: File path where the ISO seed file should be written.
        hostname: VM hostname.
        username: Default username.
        ssh_public_key: Optional SSH public key.
        password: Optional user password.
        run_commands: Optional startup commands.

    Returns:
        Dict indicating success status, ISO path, and cloud-init metadata summary.
    """
    try:
        user_data, meta_data = generate_cloud_init_config(
            hostname=hostname,
            username=username,
            ssh_public_key=ssh_public_key,
            password=password,
            run_commands=run_commands,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            user_data_path = Path(temp_dir) / "user-data"
            meta_data_path = Path(temp_dir) / "meta-data"

            user_data_path.write_text(user_data, encoding="utf-8")
            meta_data_path.write_text(meta_data, encoding="utf-8")

            # Check if mkisofs or genisoimage is available
            mkisofs_cmd = shutil.which("mkisofs") or shutil.which("genisoimage") or shutil.which("oscdimg")

            out_path = Path(output_iso_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            if mkisofs_cmd:
                cmd = [
                    mkisofs_cmd,
                    "-output",
                    str(out_path),
                    "-volid",
                    "cidata",
                    "-joliet",
                    "-rock",
                    str(user_data_path),
                    str(meta_data_path),
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                iso_created = True
            else:
                # Fallback: Save directory containing user-data & meta-data
                bundle_dir = out_path.with_suffix("")
                bundle_dir.mkdir(parents=True, exist_ok=True)
                (bundle_dir / "user-data").write_text(user_data, encoding="utf-8")
                (bundle_dir / "meta-data").write_text(meta_data, encoding="utf-8")
                iso_created = False

        return {
            "success": True,
            "hostname": hostname,
            "iso_path": str(output_iso_path),
            "iso_created": iso_created,
            "user_data": user_data,
            "meta_data": meta_data,
        }
    except Exception as e:
        logger.error(f"Failed to generate cloud-init ISO: {e}")
        return {"success": False, "error": str(e)}
