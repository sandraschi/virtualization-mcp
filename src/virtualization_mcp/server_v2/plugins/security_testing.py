"""Security Testing plugin for virtualization-mcp.

This plugin provides security testing capabilities for virtual machines,
including vulnerability scanning, penetration testing, and security assessments.
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import HTTPException, status

from ..utils.security_scanner import SecurityScanner
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class SecurityTestingPlugin(BasePlugin):
    """Security Testing plugin for running security assessments on VMs."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the Security Testing plugin.

        Args:
            config: Plugin configuration dictionary
        """
        super().__init__(config)

        # Configuration
        self.reports_dir = Path(config.get("reports_dir", "./security_reports"))
        self.tools_dir = Path(config.get("tools_dir", "./security_tools"))
        self.temp_dir = Path(config.get("temp_dir", "./temp"))

        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize security scanner
        self.scanner = SecurityScanner(tools_dir=self.tools_dir, temp_dir=self.temp_dir)

        # Scan history
        self.scan_history: list[dict[str, Any]] = []

        logger.info("Security Testing plugin initialized")

    async def initialize(self) -> None:
        """Initialize the plugin."""
        if self.initialized:
            return

        await super().initialize()

        # Initialize security tools
        await self.scanner.initialize_tools()

        logger.info("Security Testing plugin initialized with tools")

    async def shutdown(self) -> None:
        """Shut down the plugin."""
        if not self.initialized:
            return

        # Clean up temporary files
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")

        await super().shutdown()
        logger.info("Security Testing plugin shut down")

    async def scan_vm(
        self,
        vm_name: str,
        scan_type: str = "basic",
        target_ips: list[str] | None = None,
        scan_ports: bool | list[int] = True,
        vulnerability_scan: bool = True,
        web_scan: bool = False,
        credentials: dict[str, str] | None = None,
        custom_script: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Perform a security scan on a virtual machine.

        Args:
            vm_name: Name or ID of the VM to scan
            scan_type: Type of scan (basic, full, custom)
            target_ips: List of IP addresses to scan (defaults to VM's IP)
            scan_ports: List of ports to scan or True for common ports
            vulnerability_scan: Whether to perform vulnerability scanning
            web_scan: Whether to scan web applications
            credentials: Credentials for authenticated scans
            custom_script: Path to a custom scanning script
            output_format: Output format (json, html, pdf, txt)

        Returns:
            Dictionary with scan results and report path
        """
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")

        # Generate a unique scan ID
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        report_path = self.reports_dir / f"{scan_id}.{output_format}"

        try:
            # Start the scan
            scan_task = asyncio.create_task(
                self._run_scan(
                    vm_name=vm_name,
                    scan_type=scan_type,
                    target_ips=target_ips,
                    scan_ports=scan_ports,
                    vulnerability_scan=vulnerability_scan,
                    web_scan=web_scan,
                    credentials=credentials,
                    custom_script=custom_script,
                    output_format=output_format,
                    report_path=report_path,
                )
            )

            # Store scan in history
            scan_info = {
                "id": scan_id,
                "vm_name": vm_name,
                "scan_type": scan_type,
                "start_time": datetime.utcnow().isoformat(),
                "status": "running",
                "report_path": str(report_path),
                "task": scan_task,
            }
            self.scan_history.append(scan_info)

            # Set up completion callback
            scan_task.add_done_callback(lambda t, s=scan_id: self._on_scan_complete(t, s))

            return {
                "status": "started",
                "scan_id": scan_id,
                "message": f"Security scan {scan_id} started for VM {vm_name}",
            }

        except Exception as e:
            logger.error(f"Failed to start security scan: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start security scan: {str(e)}",
            ) from e

    async def _run_scan(
        self,
        vm_name: str,
        scan_type: str,
        target_ips: list[str] | None,
        scan_ports: bool | list[int],
        vulnerability_scan: bool,
        web_scan: bool,
        credentials: dict[str, str] | None,
        custom_script: str | None,
        output_format: str,
        report_path: Path,
    ) -> dict[str, Any]:
        """Run the actual security scan."""
        try:
            # Get VM information
            vm_info = await self._get_vm_info(vm_name)

            # If no target IPs provided, use VM's IP
            if not target_ips and "ip_addresses" in vm_info:
                target_ips = vm_info["ip_addresses"]

            if not target_ips:
                raise ValueError("No target IPs specified and VM has no IP addresses")

            # Run the scan
            results = await self.scanner.run_scan(
                target_ips=target_ips,
                scan_type=scan_type,
                scan_ports=scan_ports,
                vulnerability_scan=vulnerability_scan,
                web_scan=web_scan,
                credentials=credentials,
                custom_script=custom_script,
                output_format=output_format,
                output_file=str(report_path),
            )

            return {"status": "completed", "results": results, "report_path": str(report_path)}

        except Exception as e:
            logger.error(f"Error during security scan: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "report_path": str(report_path) if report_path.exists() else None,
            }

    def _on_scan_complete(self, task: asyncio.Task, scan_id: str) -> None:
        """Handle scan completion."""
        try:
            result = task.result()

            # Update scan history
            for scan in self.scan_history:
                if scan["id"] == scan_id:
                    scan.update(
                        {
                            "status": result.get("status", "unknown"),
                            "end_time": datetime.utcnow().isoformat(),
                            "result": result.get("results"),
                            "error": result.get("error"),
                        }
                    )
                    break

            logger.info(f"Security scan {scan_id} completed with status: {result.get('status')}")

        except Exception as e:
            logger.error(f"Error in scan completion handler: {e}", exc_info=True)

    async def get_scan_status(self, scan_id: str) -> dict[str, Any]:
        """Get the status of a security scan."""
        for scan in self.scan_history:
            if scan["id"] == scan_id:
                return scan

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan with ID {scan_id} not found"
        )

    async def list_scans(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent security scans."""
        return self.scan_history[-limit:]

    async def get_scan_report(self, scan_id: str) -> dict[str, Any]:
        """Get the full report for a security scan."""
        scan = next((s for s in self.scan_history if s["id"] == scan_id), None)

        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan with ID {scan_id} not found"
            )

        report_path = Path(scan["report_path"])
        if not report_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file not found for scan {scan_id}",
            )

        try:
            async with aiofiles.open(report_path) as f:
                content = await f.read()

            return {
                "scan_id": scan_id,
                "status": scan.get("status", "unknown"),
                "report": content,
                "format": report_path.suffix.lstrip("."),
            }

        except Exception as e:
            logger.error(f"Failed to read scan report: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read scan report: {str(e)}",
            ) from e

    async def _get_vm_info(self, vm_name: str) -> dict[str, Any]:
        """Get information about a VM.

        This is a placeholder method that should be implemented to get VM information
        from the virtualization platform.
        """
        # TODO: Implement actual VM info retrieval
        return {
            "id": "vm-123",
            "name": vm_name,
            "status": "running",
            "ip_addresses": ["192.168.1.100"],
            "os": "Linux",
            "memory_mb": 4096,
            "cpu_count": 2,
        }
