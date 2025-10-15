"""
Network Analyzer Tools for virtualization-mcp.

This module provides network traffic analysis and monitoring tools.
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TrafficAlertLevel(str, Enum):
    """Severity levels for network traffic alerts."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrafficAlert(BaseModel):
    """Model representing a network traffic alert."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    description: str
    level: TrafficAlertLevel
    source_ip: str
    dest_ip: str
    protocol: str


class NetworkAnalyzer:
    """Network traffic analyzer for monitoring and alerting on network activity."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the NetworkAnalyzer.

        Args:
            config: Configuration dictionary with optional keys:
                - update_interval: Seconds between analysis cycles (default: 5)
                - max_alerts: Maximum number of alerts to keep in memory (default: 1000)
        """
        config = config or {}
        self.update_interval = config.get("update_interval", 5)
        self.max_alerts = config.get("max_alerts", 1000)

        # State
        self.is_analyzing = False
        self.analysis_task: asyncio.Task | None = None
        self.alerts: deque[TrafficAlert] = deque(maxlen=self.max_alerts)
        self.websockets: set[Any] = set()
        self.traffic_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"packets": 0, "bytes": 0, "connections": 0}
        )
        self.alert_counters = {level.value: 0 for level in TrafficAlertLevel}

    async def start_analysis(self) -> None:
        """Start the network traffic analysis in the background."""
        if self.is_analyzing:
            logger.warning("Network analysis is already running")
            return

        self.is_analyzing = True
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("Network analysis started")

    async def stop_analysis(self) -> None:
        """Stop the network traffic analysis."""
        if not self.is_analyzing or not self.analysis_task:
            return

        self.is_analyzing = False
        self.analysis_task.cancel()

        try:
            await self.analysis_task
        except asyncio.CancelledError:
            pass

        logger.info("Network analysis stopped")

    async def _analysis_loop(self) -> None:
        """Background task that performs periodic network analysis."""
        while self.is_analyzing:
            try:
                # Simulate network traffic analysis
                # In a real implementation, this would analyze actual network traffic
                await asyncio.sleep(self.update_interval)

                # Check for unusual traffic patterns
                self._check_traffic_patterns()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in network analysis loop: {e}")
                await asyncio.sleep(5)  # Prevent tight loop on errors

    def _check_traffic_patterns(self) -> None:
        """Check for unusual traffic patterns and generate alerts if needed."""
        # In a real implementation, this would analyze traffic patterns
        # and generate alerts for suspicious activity
        pass

    async def add_alert(
        self,
        title: str,
        description: str,
        level: TrafficAlertLevel,
        source_ip: str,
        dest_ip: str,
        protocol: str,
    ) -> TrafficAlert:
        """Add a new network traffic alert.

        Args:
            title: Short title for the alert
            description: Detailed description of the alert
            level: Severity level of the alert
            source_ip: Source IP address
            dest_ip: Destination IP address
            protocol: Network protocol (e.g., 'tcp', 'udp')

        Returns:
            The created TrafficAlert instance
        """
        alert_id = f"alert_{len(self.alerts) + 1}_{datetime.utcnow().timestamp()}"
        alert = TrafficAlert(
            id=alert_id,
            title=title,
            description=description,
            level=level,
            source_ip=source_ip,
            dest_ip=dest_ip,
            protocol=protocol,
        )

        self.alerts.append(alert)
        self.alert_counters[level.value] += 1

        # Notify WebSocket clients
        await self._notify_websockets(alert)

        return alert

    def get_alerts(
        self,
        limit: int = 100,
        level: TrafficAlertLevel | None = None,
        source_ip: str | None = None,
        dest_ip: str | None = None,
    ) -> list[TrafficAlert]:
        """Get filtered network traffic alerts.

        Args:
            limit: Maximum number of alerts to return
            level: Filter by alert level
            source_ip: Filter by source IP
            dest_ip: Filter by destination IP

        Returns:
            List of matching TrafficAlert objects
        """
        alerts = list(self.alerts)

        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if source_ip is not None:
            alerts = [a for a in alerts if a.source_ip == source_ip]
        if dest_ip is not None:
            alerts = [a for a in alerts if a.dest_ip == dest_ip]

        return alerts[-limit:]

    def get_alert_stats(self) -> dict[str, Any]:
        """Get statistics about network traffic alerts.

        Returns:
            Dictionary containing alert statistics
        """
        return {
            "total_alerts": len(self.alerts),
            "alert_counts": self.alert_counters,
            "last_alert": self.alerts[-1].dict() if self.alerts else None,
        }

    async def _notify_websockets(self, alert: TrafficAlert) -> None:
        """Notify all connected WebSocket clients about a new alert."""
        if not self.websockets:
            return

        message = alert.dict()
        message["type"] = "alert"

        for websocket in list(self.websockets):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.websockets.discard(websocket)

    async def register_websocket(self, websocket: Any) -> None:
        """Register a WebSocket connection to receive real-time alerts.

        Args:
            websocket: WebSocket connection object
        """
        self.websockets.add(websocket)
        logger.debug(f"New WebSocket connection registered. Total: {len(self.websockets)}")

    async def unregister_websocket(self, websocket: Any) -> None:
        """Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection object to unregister
        """
        if websocket in self.websockets:
            self.websockets.remove(websocket)
            logger.debug(f"WebSocket connection unregistered. Remaining: {len(self.websockets)}")


# Create a singleton instance
network_analyzer = NetworkAnalyzer()

# Export the tool functions
start_analysis = network_analyzer.start_analysis
stop_analysis = network_analyzer.stop_analysis
add_alert = network_analyzer.add_alert
get_alerts = network_analyzer.get_alerts
get_alert_stats = network_analyzer.get_alert_stats
register_websocket = network_analyzer.register_websocket
unregister_websocket = network_analyzer.unregister_websocket

# Export the network analyzer for advanced usage
__all__ = [
    "TrafficAlertLevel",
    "TrafficAlert",
    "NetworkAnalyzer",
    "network_analyzer",
    "start_analysis",
    "stop_analysis",
    "add_alert",
    "get_alerts",
    "get_alert_stats",
    "register_websocket",
    "unregister_websocket",
]
