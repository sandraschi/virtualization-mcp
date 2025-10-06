"""
Network Tools

This package contains tools for managing and analyzing virtual network configurations
and monitoring network traffic.
"""

from .network_tools import (
    configure_network_adapter,
    list_host_network_interfaces,
    create_nat_network,
    remove_nat_network,
    list_nat_networks,
    add_port_forwarding,
    remove_port_forwarding,
    list_port_forwarding_rules,
    list_hostonly_networks,
    create_hostonly_network,
    remove_hostonly_network
)

from .network_analyzer_tools import (
    TrafficAlertLevel,
    TrafficAlert,
    NetworkAnalyzer,
    network_analyzer,
    start_analysis,
    stop_analysis,
    add_alert,
    get_alerts,
    get_alert_stats,
    register_websocket,
    unregister_websocket
)

__all__ = [
    # Network Configuration Tools
    'configure_network_adapter',
    'list_host_network_interfaces',
    'create_nat_network',
    'remove_nat_network',
    'list_nat_networks',
    'add_port_forwarding',
    'remove_port_forwarding',
    'list_port_forwarding_rules',
    'list_hostonly_networks',
    'create_hostonly_network',
    'remove_hostonly_network',
    
    # Network Analyzer Tools
    'TrafficAlertLevel',
    'TrafficAlert',
    'NetworkAnalyzer',
    'network_analyzer',
    'start_analysis',
    'stop_analysis',
    'add_alert',
    'get_alerts',
    'get_alert_stats',
    'register_websocket',
    'unregister_websocket'
]
