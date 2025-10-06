"""
Metrics Collection and Monitoring Tools for VBoxMCP

This module provides tools for collecting and monitoring metrics related to VBoxMCP operations.
Combines functionality from the original metrics_tools.py and monitoring_tools.py.
"""

import time
import asyncio
import psutil
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import start_http_server, Gauge, Counter, generate_latest

logger = logging.getLogger(__name__)

@dataclass
class VMMetrics:
    """Metrics specific to a single VM."""
    vm_id: str
    cpu_usage: float = 0.0  # Percentage
    memory_usage: float = 0.0  # MB
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    network_in_bytes: int = 0
    network_out_bytes: int = 0
    timestamp: float = field(default_factory=time.time)

@dataclass
class SystemMetrics:
    """System-wide metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0
    timestamp: float = field(default_factory=time.time)

class MetricsManager:
    """Manages collection and retrieval of system and VM metrics."""
    
    def __init__(self):
        self.vm_metrics: Dict[str, List[VMMetrics]] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.api_requests: List[dict] = []
        self.errors: List[dict] = []
        self.lock = Lock()
        self._last_network_io = psutil.net_io_counters()
        self._last_disk_io = psutil.disk_io_counters()
        
    def record_vm_metrics(self, vm_id: str, metrics: Dict[str, Any]) -> None:
        """Record metrics for a specific VM."""
        with self.lock:
            if vm_id not in self.vm_metrics:
                self.vm_metrics[vm_id] = []
                
            vm_metric = VMMetrics(
                vm_id=vm_id,
                cpu_usage=metrics.get('cpu_usage', 0.0),
                memory_usage=metrics.get('memory_usage', 0.0),
                disk_read_bytes=metrics.get('disk_read_bytes', 0),
                disk_write_bytes=metrics.get('disk_write_bytes', 0),
                network_in_bytes=metrics.get('network_in_bytes', 0),
                network_out_bytes=metrics.get('network_out_bytes', 0)
            )
            
            self.vm_metrics[vm_id].append(vm_metric)
            
            # Keep only the last 1000 data points per VM
            if len(self.vm_metrics[vm_id]) > 1000:
                self.vm_metrics[vm_id] = self.vm_metrics[vm_id][-1000:]
    
    def update_system_metrics(self) -> None:
        """Update system-wide metrics."""
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get disk usage (primary disk)
        disk_usage = psutil.disk_usage('/').percent
        
        # Get network I/O
        net_io = psutil.net_io_counters()
        sent_bytes = net_io.bytes_sent - self._last_network_io.bytes_sent
        recv_bytes = net_io.bytes_recv - self._last_network_io.bytes_recv
        self._last_network_io = net_io
        
        # Create and store system metrics
        system_metric = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk_usage,
            network_sent_bytes=sent_bytes,
            network_recv_bytes=recv_bytes
        )
        
        with self.lock:
            self.system_metrics.append(system_metric)
            # Keep only the last 1000 data points
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]
    
    def record_api_request(self, endpoint: str, method: str, status_code: int, 
                         processing_time: float) -> None:
        """Record an API request for monitoring."""
        with self.lock:
            self.api_requests.append({
                'timestamp': time.time(),
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'processing_time': processing_time
            })
            # Keep only the last 1000 requests
            if len(self.api_requests) > 1000:
                self.api_requests = self.api_requests[-1000:]
    
    def record_error(self, error_type: str, message: str, 
                    details: Optional[Dict] = None) -> None:
        """Record an error that occurred."""
        with self.lock:
            self.errors.append({
                'timestamp': time.time(),
                'error_type': error_type,
                'message': message,
                'details': details or {}
            })
            # Keep only the last 1000 errors
            if len(self.errors) > 1000:
                self.errors = self.errors[-1000:]
    
    def get_metrics(self, time_range: int = 300) -> Dict[str, Any]:
        """Get metrics from the last 'time_range' seconds."""
        now = time.time()
        cutoff = now - time_range
        
        with self.lock:
            # Filter system metrics by time range
            system_metrics = [
                m for m in self.system_metrics 
                if m.timestamp >= cutoff
            ]
            
            # Filter VM metrics by time range
            vm_metrics = {}
            for vm_id, metrics in self.vm_metrics.items():
                filtered = [m for m in metrics if m.timestamp >= cutoff]
                if filtered:
                    vm_metrics[vm_id] = filtered
            
            # Filter API requests
            api_requests = [
                r for r in self.api_requests 
                if r['timestamp'] >= cutoff
            ]
            
            # Filter errors
            errors = [e for e in self.errors if e['timestamp'] >= cutoff]
            
            return {
                'system': system_metrics,
                'vms': vm_metrics,
                'api_requests': api_requests,
                'errors': errors,
                'timestamp': now
            }

class PrometheusMetrics:
    """Handles Prometheus metrics collection and exposure."""
    
    def __init__(self, port: int = 9090):
        self.port = port
        self.metrics = {}
        self._register_metrics()
        
    def _register_metrics(self):
        """Register all Prometheus metrics."""
        self.metrics = {
            'vm_cpu_usage': Gauge('vboxmcp_vm_cpu_usage', 'CPU usage per VM', ['vm_id']),
            'vm_memory_usage': Gauge('vboxmcp_vm_memory_usage', 'Memory usage per VM', ['vm_id']),
            'system_cpu_usage': Gauge('vboxmcp_system_cpu_usage', 'System CPU usage'),
            'system_memory_usage': Gauge('vboxmcp_system_memory_usage', 'System memory usage'),
            'api_requests_total': Counter('vboxmcp_api_requests_total', 'Total API requests', ['endpoint', 'method', 'status']),
            'errors_total': Counter('vboxmcp_errors_total', 'Total errors', ['error_type'])
        }
    
    def start_http_server(self):
        """Start the Prometheus metrics HTTP server."""
        start_http_server(self.port)
        logger.info(f"Prometheus metrics server started on port {self.port}")
    
    def update_vm_metrics(self, vm_id: str, metrics: Dict[str, float]):
        """Update VM metrics."""
        self.metrics['vm_cpu_usage'].labels(vm_id=vm_id).set(metrics.get('cpu_usage', 0))
        self.metrics['vm_memory_usage'].labels(vm_id=vm_id).set(metrics.get('memory_usage', 0))
    
    def update_system_metrics(self):
        """Update system metrics."""
        self.metrics['system_cpu_usage'].set(psutil.cpu_percent())
        self.metrics['system_memory_usage'].set(psutil.virtual_memory().percent)
    
    def record_api_request(self, endpoint: str, method: str, status_code: int):
        """Record an API request."""
        status = f"{status_code}"
        self.metrics['api_requests_total'].labels(
            endpoint=endpoint, 
            method=method.lower(), 
            status=status
        ).inc()
    
    def record_error(self, error_type: str):
        """Record an error."""
        self.metrics['errors_total'].labels(error_type=error_type).inc()

# Global instances
metrics_manager = MetricsManager()
prometheus_metrics = PrometheusMetrics()

def start_metrics_server(host: str = "0.0.0.0", port: int = 8000, prometheus_port: int = 9090) -> FastAPI:
    """
    Start a FastAPI server to expose metrics via HTTP.
    
    Args:
        host: Host to bind the server to
        port: Port for the API server
        prometheus_port: Port for Prometheus metrics
    """
    app = FastAPI()
    
    # Start Prometheus metrics server in a separate thread
    prometheus_metrics.port = prometheus_port
    prometheus_thread = threading.Thread(
        target=prometheus_metrics.start_http_server,
        daemon=True
    )
    prometheus_thread.start()
    
    @app.get("/metrics")
    async def get_metrics():
        """Get all metrics in JSON format."""
        return JSONResponse(content=metrics_manager.get_metrics())
    
    @app.get("/prometheus")
    async def get_prometheus_metrics():
        """Get metrics in Prometheus format."""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )
    
    # Start the FastAPI server in a separate thread
    def run_server():
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    logger.info(f"Metrics server started on http://{host}:{port}")
    logger.info(f"Prometheus metrics available on :{prometheus_port}/metrics")
    
    return app

# Convenience functions for metrics collection
def record_api_request(endpoint: str, method: str, status_code: int, 
                     processing_time: Optional[float] = None) -> None:
    """
    Record an API request in both the metrics manager and Prometheus.
    
    Args:
        endpoint: The API endpoint that was called
        method: HTTP method (GET, POST, etc.)
        status_code: HTTP status code
        processing_time: Optional processing time in seconds
    """
    metrics_manager.record_api_request(endpoint, method, status_code, processing_time or 0)
    prometheus_metrics.record_api_request(endpoint, method, status_code)

def record_error(error_type: str, message: str, 
               details: Optional[Dict] = None) -> None:
    """
    Record an error in both the metrics manager and Prometheus.
    
    Args:
        error_type: Type/category of the error
        message: Error message
        details: Optional additional error details
    """
    metrics_manager.record_error(error_type, message, details or {})
    prometheus_metrics.record_error(error_type)

def update_vm_metrics(vm_id: str, metrics: Dict[str, Any]) -> None:
    """
    Update VM metrics in both the metrics manager and Prometheus.
    
    Args:
        vm_id: ID of the virtual machine
        metrics: Dictionary of metric names and values
    """
    metrics_manager.record_vm_metrics(vm_id, metrics)
    prometheus_metrics.update_vm_metrics(vm_id, metrics)

def update_system_metrics() -> None:
    """Update system metrics in both the metrics manager and Prometheus."""
    metrics_manager.update_system_metrics()
    prometheus_metrics.update_system_metrics()

def get_metrics(time_range: int = 300) -> Dict[str, Any]:
    """
    Get collected metrics.
    
    Args:
        time_range: Time range in seconds to get metrics for
        
    Returns:
        Dictionary containing all collected metrics
    """
    return metrics_manager.get_metrics(time_range)

# Add FastAPI middleware for request tracking
class MetricsMiddleware:
    """Middleware to track request metrics."""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        status_code = 500  # Default to error status
        
        async def wrapped_send(message):
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
            await send(message)
            
        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            record_error("http_error", str(e))
            raise
        finally:
            processing_time = time.time() - start_time
            request = Request(scope)
            record_api_request(
                endpoint=str(request.url.path),
                method=request.method,
                status_code=status_code,
                processing_time=processing_time
            )
