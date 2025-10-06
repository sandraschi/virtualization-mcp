"""
VM Metrics and Monitoring Module

This module provides comprehensive monitoring of VM performance metrics including
CPU, memory, disk, and network usage. It also supports collecting historical
metrics and generating performance reports.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Constants for metrics collection
METRICS_INTERVAL = 5  # seconds
MAX_HISTORY = 3600 // METRICS_INTERVAL  # 1 hour of history

def metrics_operation(func):
    """Decorator for metrics operations with error handling and logging."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Metrics operation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation": func.__name__,
                "vm_name": kwargs.get('vm_name', 'unknown')
            }
    return wrapper

@dataclass
class VMMetricSample:
    """Data class for storing a single metric sample."""
    timestamp: float
    # CPU metrics
    cpu_usage: float  # percentage
    cpu_system_usage: float  # system CPU usage percentage
    cpu_user_usage: float  # user CPU usage percentage
    cpu_idle_usage: float  # idle CPU percentage
    cpu_count: int  # number of CPUs
    # Memory metrics
    memory_usage: int  # bytes
    memory_total: int  # total memory in bytes
    memory_free: int  # free memory in bytes
    memory_cached: int  # cached memory in bytes
    memory_buffer: int  # buffered memory in bytes
    # Disk metrics
    disk_read_bytes: int  # total bytes read
    disk_write_bytes: int  # total bytes written
    disk_read_ops: int  # number of read operations
    disk_write_ops: int  # number of write operations
    disk_latency_avg: float  # average disk latency in ms
    # Network metrics
    network_in_bytes: int  # total bytes received
    network_out_bytes: int  # total bytes sent
    network_in_packets: int  # packets received
    network_out_packets: int  # packets sent
    network_in_errors: int  # receive errors
    network_out_errors: int  # send errors
    # System metrics
    process_count: int  # number of processes
    thread_count: int  # number of threads
    handle_count: int  # number of handles
    # Performance counters
    context_switches: int  # context switches per second
    page_faults: int  # page faults per second
    swap_usage: int  # swap usage in bytes
    swap_total: int  # total swap space in bytes

class VMMetricsMixin:
    """
    Mixin class providing VM metrics and monitoring methods.
    
    This class handles the collection and reporting of performance metrics
    for virtual machines, including CPU, memory, disk, and network usage.
    """
    
    def __init__(self, vm_service):
        """
        Initialize with a reference to the parent VMService.
        
        Args:
            vm_service: Reference to the parent VMService instance
        """
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations
        
        # In-memory storage for metrics history
        self._metrics_history = {}  # vm_name -> list[VMMetricSample]
        self._last_metrics_update = {}
    
    @metrics_operation
    def get_vm_metrics(self, vm_name: str) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for a virtual machine.
        
        This method returns the current performance metrics for the specified VM,
        including CPU usage, memory usage, disk I/O, and network statistics.
        
        API Endpoint: GET /vms/{vm_name}/metrics
        
        Args:
            vm_name: Name of the VM to get metrics for
            
        Returns:
            Dictionary containing the current metrics for the VM
            
        Raises:
            ValueError: If the VM name is not provided
            RuntimeError: If the VM is not found or metrics cannot be retrieved
            
        Example:
            ```python
            # Get metrics for a VM
            metrics = metrics.get_vm_metrics("my-vm")
            print(f"CPU Usage: {metrics['cpu_usage_percent']}%")
            print(f"Memory Usage: {metrics['memory_used_mb']} MB")
            ```
        """
        if not vm_name:
            raise ValueError("VM name is required")
        
        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")
        
        # Get the session
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for reading
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Shared)
            
            # Get machine and console
            machine = session.machine
            console = session.console
            
            # Get CPU metrics
            cpu_usage_percent = 0.0
            cpu_system_usage = 0.0
            cpu_user_usage = 0.0
            cpu_idle_usage = 100.0
            cpu_count = 1
            
            if hasattr(console, 'PERFCOUNTER'):
                try:
                    # Get overall CPU usage
                    cpu_usage_percent = console.get_cpu_usage(0)  # CPU 0
                    
                    # Get detailed CPU stats if available
                    if hasattr(console, 'get_cpu_load'):
                        cpu_load = console.get_cpu_load(0)
                        cpu_user_usage = cpu_load.user * 100
                        cpu_system_usage = cpu_load.system * 100
                        cpu_idle_usage = cpu_load.idle * 100
                    
                    # Get CPU count
                    cpu_count = machine.CPU_count
                except Exception as e:
                    logger.warning(f"Could not get detailed CPU metrics: {e}")
                    pass
            
            # Get memory metrics
            memory_total = machine.memory_size
            memory_free = 0
            memory_cached = 0
            memory_buffer = 0
            swap_usage = 0
            swap_total = 0
            
            if hasattr(console, 'get_memory_stats'):
                try:
                    mem_stats = console.get_memory_stats()
                    memory_free = mem_stats.get('free_ram', 0)
                    memory_cached = mem_stats.get('cached_ram', 0)
                    memory_buffer = mem_stats.get('buffers', 0)
                    swap_usage = mem_stats.get('used_swap', 0)
                    swap_total = mem_stats.get('total_swap', 0)
                except Exception as e:
                    logger.warning(f"Could not get detailed memory stats: {e}")
                    try:
                        memory_free = console.get_memory_usage()
                    except:
                        pass
            
            memory_used = memory_total - memory_free - memory_cached - memory_buffer
            if memory_used < 0:
                memory_used = memory_total - memory_free  # Fallback if calculation is invalid
            
            # Get disk metrics
            disk_read_bytes = 0
            disk_write_bytes = 0
            disk_read_ops = 0
            disk_write_ops = 0
            disk_latency_total = 0
            disk_count = 0
            
            for i in range(machine.get_storage_controller_count()):
                controller = machine.get_storage_controller_by_index(i)
                for port in range(controller.port_count):
                    for device in range(controller.max_devices_per_port):
                        try:
                            attachment = controller.get_device_attachment(port, device)
                            if attachment and attachment.medium:
                                disk = attachment.medium
                                disk_read_bytes += getattr(disk, 'bytes_read', 0)
                                disk_write_bytes += getattr(disk, 'bytes_written', 0)
                                disk_read_ops += getattr(disk, 'read_operations', 0)
                                disk_write_ops += getattr(disk, 'write_operations', 0)
                                
                                # Calculate average latency if available
                                if hasattr(disk, 'total_read_time') and hasattr(disk, 'total_write_time'):
                                    total_time = getattr(disk, 'total_read_time', 0) + getattr(disk, 'total_write_time', 0)
                                    total_ops = getattr(disk, 'read_operations', 0) + getattr(disk, 'write_operations', 0)
                                    if total_ops > 0:
                                        disk_latency_total += (total_time / total_ops) * 1000  # Convert to ms
                                        disk_count += 1
                        except Exception as e:
                            logger.debug(f"Error getting disk metrics: {e}")
                            continue
            
            # Calculate average disk latency
            disk_latency_avg = disk_latency_total / disk_count if disk_count > 0 else 0
            
            # Get network metrics
            network_in_bytes = 0
            network_out_bytes = 0
            network_in_packets = 0
            network_out_packets = 0
            network_in_errors = 0
            network_out_errors = 0
            
            for i in range(machine.get_network_adapter_count()):
                try:
                    adapter = machine.get_network_adapter(i)
                    if adapter.enabled:
                        network_in_bytes += getattr(adapter, 'bytes_received', 0)
                        network_out_bytes += getattr(adapter, 'bytes_sent', 0)
                        network_in_packets += getattr(adapter, 'packets_received', 0)
                        network_out_packets += getattr(adapter, 'packets_sent', 0)
                        network_in_errors += getattr(adapter, 'receive_errors', 0)
                        network_out_errors += getattr(adapter, 'send_errors', 0)
                except Exception as e:
                    logger.debug(f"Error getting network adapter {i} metrics: {e}")
                    continue
            
            # Get process and system metrics
            process_count = 0
            thread_count = 0
            handle_count = 0
            context_switches = 0
            page_faults = 0
            
            if hasattr(console, 'get_process_stats'):
                try:
                    stats = console.get_process_stats()
                    process_count = stats.get('processes', 0)
                    thread_count = stats.get('threads', 0)
                    handle_count = stats.get('handles', 0)
                    context_switches = stats.get('context_switches', 0)
                    page_faults = stats.get('page_faults', 0)
                except Exception as e:
                    logger.debug(f"Could not get process stats: {e}")
            
            # Create metrics sample with all collected data
            timestamp = time.time()
            sample = VMMetricSample(
                timestamp=timestamp,
                # CPU metrics
                cpu_usage=cpu_usage_percent,
                cpu_system_usage=cpu_system_usage,
                cpu_user_usage=cpu_user_usage,
                cpu_idle_usage=cpu_idle_usage,
                cpu_count=cpu_count,
                # Memory metrics
                memory_usage=memory_used,
                memory_total=memory_total,
                memory_free=memory_free,
                memory_cached=memory_cached,
                memory_buffer=memory_buffer,
                # Disk metrics
                disk_read_bytes=disk_read_bytes,
                disk_write_bytes=disk_write_bytes,
                disk_read_ops=disk_read_ops,
                disk_write_ops=disk_write_ops,
                disk_latency_avg=disk_latency_avg,
                # Network metrics
                network_in_bytes=network_in_bytes,
                network_out_bytes=network_out_bytes,
                network_in_packets=network_in_packets,
                network_out_packets=network_out_packets,
                network_in_errors=network_in_errors,
                network_out_errors=network_out_errors,
                # System metrics
                process_count=process_count,
                thread_count=thread_count,
                handle_count=handle_count,
                # Performance counters
                context_switches=context_switches,
                page_faults=page_faults,
                swap_usage=swap_usage,
                swap_total=swap_total
            )
            
            # Update metrics history
            if vm_name not in self._metrics_history:
                self._metrics_history[vm_name] = []
            self._metrics_history[vm_name].append(sample)
            
            # Trim history if needed
            if len(self._metrics_history[vm_name]) > MAX_HISTORY:
                self._metrics_history[vm_name].pop(0)
            
            self._last_metrics_update[vm_name] = timestamp
            
            # Return current metrics
            return {
                "status": "success",
                "vm_name": vm_name,
                "timestamp": timestamp,
                "cpu_usage_percent": cpu_usage_percent,
                "memory_total_mb": memory // (1024 * 1024),
                "memory_used_mb": memory_used // (1024 * 1024),
                "memory_free_mb": memory_free // (1024 * 1024),
                "disk_read_mb": disk_read_bytes // (1024 * 1024),
                "disk_write_mb": disk_write_bytes // (1024 * 1024),
                "network_in_mb": network_in_bytes // (1024 * 1024),
                "network_out_mb": network_out_bytes // (1024 * 1024)
            }
            
        finally:
            session.unlock_machine()
    
    @metrics_operation
    def get_cpu_usage(self, vm_name: str) -> Dict[str, Any]:
        """
        Get CPU usage metrics for a VM.
        
        This method returns the current CPU usage for the specified VM.
        
        API Endpoint: GET /vms/{vm_name}/metrics/cpu
        
        Args:
            vm_name: Name of the VM to get CPU metrics for
            
        Returns:
            Dictionary containing CPU usage metrics
            
        Example:
            ```python
            # Get CPU usage for a VM
            cpu_metrics = metrics.get_cpu_usage("my-vm")
            print(f"CPU Usage: {cpu_metrics['cpu_usage_percent']}%")
            ```
        """
        metrics = self.get_vm_metrics(vm_name)
        if metrics.get("status") != "success":
            return metrics
        
        return {
            "status": "success",
            "vm_name": vm_name,
            "timestamp": metrics["timestamp"],
            "cpu_usage_percent": metrics["cpu_usage_percent"],
            "cpu_count": metrics.get("cpu_count", 1)
        }
    
    @metrics_operation
    def get_memory_usage(self, vm_name: str) -> Dict[str, Any]:
        """
        Get memory usage metrics for a VM.
        
        This method returns the current memory usage for the specified VM.
        
        API Endpoint: GET /vms/{vm_name}/metrics/memory
        
        Args:
            vm_name: Name of the VM to get memory metrics for
            
        Returns:
            Dictionary containing memory usage metrics
            
        Example:
            ```python
            # Get memory usage for a VM
            mem_metrics = metrics.get_memory_usage("my-vm")
            print(f"Memory Usage: {mem_metrics['memory_used_mb']} MB / {mem_metrics['memory_total_mb']} MB")
            ```
        """
        metrics = self.get_vm_metrics(vm_name)
        if metrics.get("status") != "success":
            return metrics
        
        return {
            "status": "success",
            "vm_name": vm_name,
            "timestamp": metrics["timestamp"],
            "memory_total_mb": metrics["memory_total_mb"],
            "memory_used_mb": metrics["memory_used_mb"],
            "memory_free_mb": metrics["memory_free_mb"],
            "memory_usage_percent": (metrics["memory_used_mb"] / metrics["memory_total_mb"]) * 100
            if metrics["memory_total_mb"] > 0 else 0
        }
    
    def get_disk_io(self, vm_name: str) -> Dict[str, Any]:
        """Get disk I/O metrics for a VM."""
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to get disk I/O for VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def get_network_io(self, vm_name: str) -> Dict[str, Any]:
        """Get network I/O metrics for a VM."""
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to get network I/O for VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
