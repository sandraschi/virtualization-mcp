"""
Network Tools

This package contains tools for managing and analyzing virtual network configurations
and monitoring network traffic.
"""

from .network_analyzer_tools import (
    NetworkAnalyzer,
    TrafficAlert,
    TrafficAlertLevel,
    add_alert,
    get_alert_stats,
    get_alerts,
    network_analyzer,
    register_websocket,
    start_analysis,
    stop_analysis,
    unregister_websocket,
)
from .network_tools import (
    add_port_forwarding,
    configure_network_adapter,
    create_hostonly_network,
    create_nat_network,
    list_host_network_interfaces,
    list_hostonly_networks,
    list_nat_networks,
    list_port_forwarding_rules,
    remove_hostonly_network,
    remove_nat_network,
    remove_port_forwarding,
)

__all__ = [
    # Network Configuration Tools
    "configure_network_adapter",
    "list_host_network_interfaces",
    "create_nat_network",
    "remove_nat_network",
    "list_nat_networks",
    "add_port_forwarding",
    "remove_port_forwarding",
    "list_port_forwarding_rules",
    "list_hostonly_networks",
    "create_hostonly_network",
    "remove_hostonly_network",
    # Network Analyzer Tools
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
