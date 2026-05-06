"""
virtualization-mcp Tools Package

This package contains all the tools for virtualization-mcp organized into logical modules.
"""

# Import the registration function
# Import development tools
from virtualization_mcp.tools.dev import (
    ParameterDocumentation,
    ToolDocumentation,
    document_tool,
    get_api_documentation,
    get_openapi_schema,
)

# Import tool modules
from virtualization_mcp.tools.example_tools import (
    analyze_file,
    create_task,
    get_counter,
    greet,
    list_tasks,
)

# Import monitoring tools
from virtualization_mcp.tools.monitoring import (
    MetricsManager,
    get_metrics,
    metrics_manager,
    record_api_request,
    record_error,
    start_metrics_server,
    update_system_metrics,
    update_vm_metrics,
)

# Import network tools
from virtualization_mcp.tools.network import (
    NetworkAnalyzer,
    TrafficAlert,
    # Network Analyzer
    TrafficAlertLevel,
    add_alert,
    add_port_forwarding,
    # Network Configuration
    configure_network_adapter,
    create_hostonly_network,
    create_nat_network,
    get_alert_stats,
    get_alerts,
    list_host_network_interfaces,
    list_hostonly_networks,
    list_nat_networks,
    list_port_forwarding_rules,
    network_analyzer,
    register_websocket,
    remove_hostonly_network,
    remove_nat_network,
    remove_port_forwarding,
    start_analysis,
    stop_analysis,
    unregister_websocket,
)
from virtualization_mcp.tools.register_tools import register_all_tools

# Import security tools
from virtualization_mcp.tools.security import (
    AnalysisResult,
    # Malware Analysis Tools
    AnalysisStatus,
    Detection,
    SecurityFinding,
    SecurityReport,  # Backward compatibility
    SecurityTester,
    SecurityTestResult,
    # AI Security Tools
    SecurityThreatLevel,  # Backward compatibility
    TestSeverity,
    # Security Testing Tools
    TestStatus,
    ThreatLevel,
    cancel_test,
    delete_analysis,
    generate_report,
    get_analysis,
    get_security_scan_status,
    get_test_status,
    list_analyses,
    list_available_tools,
    list_quarantine,
    run_security_scan,
    security_tester,
    start_security_scan,  # Backward compatibility
)

# Import system tools
from virtualization_mcp.tools.system import create_backup, delete_backup, list_backups

# Import VM tools
from virtualization_mcp.tools.vm import (
    VirtualMachine,
    VMDisk,
    VMNetworkAdapter,
    VMSize,
    VMSnapshot,
    # Hyper-V tools (individual tools disabled - using portmanteau)
    VMState,
    clone_vm,
    create_vm,
    delete_vm,
    # get_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
    get_vm_info,
    # list_hyperv_vms,  # Disabled - use hyperv_management portmanteau tool
    # Base VM tools
    list_vms,
    modify_vm,
    pause_vm,
    reset_vm,
    resume_vm,
    # start_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
    start_vm,
    # stop_hyperv_vm,  # Disabled - use hyperv_management portmanteau tool
    stop_vm,
)

# VM tools are imported via vm.__init__ (line 113) - no need to import again

# Re-export the registration functions and tools
__all__ = [
    "AnalysisResult",
    "AnalysisStatus",
    "Detection",
    # Monitoring Tools
    "MetricsManager",
    "NetworkAnalyzer",
    "ParameterDocumentation",
    "SecurityFinding",
    "SecurityReport",  # Backward compatibility
    "SecurityTestResult",
    "SecurityTestResult",
    "SecurityTester",
    # Security Tools
    "SecurityThreatLevel",  # Backward compatibility
    "TestSeverity",
    "TestSeverity",
    "TestStatus",
    "ThreatLevel",
    "ToolDocumentation",
    "TrafficAlert",
    # Network Analyzer Tools
    "TrafficAlertLevel",
    "VMDisk",
    "VMNetworkAdapter",
    "VMSize",
    "VMSnapshot",
    # Hyper-V Tools (individual tools disabled - using portmanteau)
    "VMState",
    "VirtualMachine",
    "add_alert",
    "add_port_forwarding",
    "analyze_file",
    "analyze_file",
    "cancel_test",
    "clone_vm",
    "clone_vm",
    # Network Configuration Tools
    "configure_network_adapter",
    # System Tools
    "create_backup",
    "create_hostonly_network",
    "create_nat_network",
    "create_task",
    "create_vm",
    "create_vm",
    "delete_analysis",
    "delete_backup",
    "delete_vm",
    "delete_vm",
    # Development Tools
    "document_tool",
    "generate_report",
    "get_alert_stats",
    "get_alerts",
    "get_analysis",
    "get_api_documentation",
    "get_counter",
    "get_metrics",
    "get_openapi_schema",
    "get_security_scan_status",
    "get_test_status",
    "get_vm_info",
    "get_vm_info",
    # Example Tools
    "greet",
    "list_analyses",
    "list_available_tools",
    "list_backups",
    "list_host_network_interfaces",
    "list_hostonly_networks",
    "list_nat_networks",
    "list_port_forwarding_rules",
    "list_quarantine",
    "list_tasks",
    # VM Tools
    "list_vms",
    # VM Tools
    "list_vms",
    "metrics_manager",
    "modify_vm",
    "modify_vm",
    "network_analyzer",
    "pause_vm",
    "pause_vm",
    "record_api_request",
    "record_error",
    "register_all_tools",
    "register_websocket",
    "remove_hostonly_network",
    "remove_nat_network",
    "remove_port_forwarding",
    "reset_vm",
    "reset_vm",
    "resume_vm",
    "resume_vm",
    "run_security_scan",
    "run_security_scan",
    "security_tester",
    "start_analysis",
    "start_metrics_server",
    "start_security_scan",  # Backward compatibility
    "start_vm",
    "start_vm",
    "stop_analysis",
    "stop_vm",
    "stop_vm",
    "unregister_websocket",
    "update_system_metrics",
    "update_vm_metrics",
    # "list_hyperv_vms",  # Disabled - use hyperv_management portmanteau tool
    # "get_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "start_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "stop_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
]
