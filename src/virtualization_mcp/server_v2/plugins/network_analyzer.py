"""Lightweight Network Traffic Analyzer plugin for virtualization-mcp."""
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Deque

from fastapi import APIRouter, HTTPException, status, WebSocket
from pydantic import BaseModel, Field

from virtualization_mcp.server_v2.plugins.base import BasePlugin
from virtualization_mcp.server_v2.plugins import register_plugin

logger = logging.getLogger(__name__)

class TrafficAlertLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TrafficAlert(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    description: str
    level: TrafficAlertLevel
    source_ip: str
    dest_ip: str
    protocol: str

@register_plugin("network_analyzer")
class NetworkAnalyzerPlugin(BasePlugin):
    """Lightweight Network Traffic Analyzer plugin."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.update_interval = config.get("update_interval", 5)
        self.max_alerts = config.get("max_alerts", 1000)
        
        # State
        self.is_analyzing = False
        self.analysis_task = None
        self.alerts: Deque[TrafficAlert] = deque(maxlen=self.max_alerts)
        self.websockets: List[WebSocket] = []
        
        # Traffic stats
        self.bytes_transferred = 0
        self.packets_processed = 0
        self.protocol_stats = defaultdict(int)
        self.host_stats = defaultdict(lambda: {"bytes_sent": 0, "bytes_received": 0})
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self) -> None:
        """Set up API routes for network analysis."""
        @self.router.get("/stats")
        async def get_stats() -> Dict[str, Any]:
            """Get current traffic statistics."""
            return {
                "bytes_transferred": self.bytes_transferred,
                "packets_processed": self.packets_processed,
                "protocols": dict(self.protocol_stats),
                "top_hosts": dict(self.host_stats)
            }
        
        @self.router.get("/alerts")
        async def get_alerts(limit: int = 100) -> List[Dict[str, Any]]:
            """Get recent traffic alerts."""
            return [alert.dict() for alert in list(self.alerts)[-limit:]]
        
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websockets.append(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
            finally:
                self.websockets.remove(websocket)
        
        @self.router.post("/start")
        async def start_analysis():
            """Start network traffic analysis."""
            if self.is_analyzing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Analysis is already running"
                )
            
            self.is_analyzing = True
            self.analysis_task = asyncio.create_task(self._analyze_network())
            return {"status": "started"}
        
        @self.router.post("/stop")
        async def stop_analysis():
            """Stop network traffic analysis."""
            if not self.is_analyzing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No analysis is currently running"
                )
            
            self.is_analyzing = False
            if self.analysis_task:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass
            
            return {"status": "stopped"}
    
    async def _analyze_network(self) -> None:
        """Simulate network traffic analysis."""
        logger.info("Starting network traffic analysis")
        
        try:
            while self.is_analyzing:
                # Simulate network traffic analysis
                await asyncio.sleep(self.update_interval)
                
                # Generate sample alert occasionally
                if self.packets_processed % 100 == 0:
                    await self._generate_sample_alert()
                
                # Update WebSocket clients
                await self._broadcast_update()
                
        except asyncio.CancelledError:
            logger.info("Network analysis stopped")
        except Exception as e:
            logger.error(f"Error in network analysis: {str(e)}", exc_info=True)
            self.is_analyzing = False
    
    async def _generate_sample_alert(self) -> None:
        """Generate a sample traffic alert."""
        alert = TrafficAlert(
            id=f"alert_{len(self.alerts) + 1}",
            title="Sample Security Alert",
            description="This is a sample security alert generated by the network analyzer.",
            level=TrafficAlertLevel.INFO,
            source_ip="192.168.1.100",
            dest_ip="8.8.8.8",
            protocol="TCP"
        )
        self.alerts.append(alert)
        
        # Log the alert
        logger.info(f"Generated alert: {alert.title}")
    
    async def _broadcast_update(self) -> None:
        """Broadcast update to all connected WebSocket clients."""
        if not self.websockets:
            return
            
        update = {
            "type": "stats_update",
            "bytes_transferred": self.bytes_transferred,
            "packets_processed": self.packets_processed,
            "alert_count": len(self.alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for websocket in list(self.websockets):
            try:
                await websocket.send_json(update)
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {str(e)}")
                if websocket in self.websockets:
                    self.websockets.remove(websocket)
    
    async def startup(self) -> None:
        """Startup tasks."""
        await super().startup()
        logger.info("Network Analyzer plugin started")
    
    async def shutdown(self) -> None:
        """Shutdown tasks."""
        self.is_analyzing = False
        
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        await super().shutdown()
        logger.info("Network Analyzer plugin stopped")
