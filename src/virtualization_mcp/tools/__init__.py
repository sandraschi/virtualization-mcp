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

# Import sandbox tools
from virtualization_mcp.tools.dev.sandbox_tools import (
    SandboxType,
    TestResult,
    cleanup_sandbox,
    create_sandbox,
    run_in_sandbox,
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
    "register_all_tools",
    # VM Tools
    "list_vms",
    "get_vm_info",
    "start_vm",
    "stop_vm",
    "create_vm",
    "delete_vm",
    "clone_vm",
    "modify_vm",
    "pause_vm",
    "resume_vm",
    "reset_vm",
    # Example Tools
    "greet",
    "create_task",
    "list_tasks",
    "get_counter",
    "analyze_file",
    # Security Tools
    "SecurityThreatLevel",  # Backward compatibility
    "TestSeverity",
    "SecurityFinding",
    "SecurityReport",  # Backward compatibility
    "SecurityTestResult",
    "start_security_scan",  # Backward compatibility
    "run_security_scan",
    "get_security_scan_status",
    "AnalysisStatus",
    "ThreatLevel",
    "Detection",
    "AnalysisResult",
    "analyze_file",
    "get_analysis",
    "list_analyses",
    "delete_analysis",
    "list_quarantine",
    "TestStatus",
    "TestSeverity",
    "SecurityTestResult",
    "SecurityTester",
    "security_tester",
    "run_security_scan",
    "get_test_status",
    "cancel_test",
    "list_available_tools",
    "generate_report",
    # System Tools
    "create_backup",
    "list_backups",
    "delete_backup",
    # Development Tools
    "document_tool",
    "get_api_documentation",
    "get_openapi_schema",
    "ParameterDocumentation",
    "ToolDocumentation",
    # Monitoring Tools
    "MetricsManager",
    "metrics_manager",
    "start_metrics_server",
    "record_api_request",
    "record_error",
    "update_vm_metrics",
    "update_system_metrics",
    "get_metrics",
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
    # VM Tools
    "list_vms",
    "get_vm_info",
    "start_vm",
    "stop_vm",
    "create_vm",
    "delete_vm",
    "clone_vm",
    "modify_vm",
    "reset_vm",
    "pause_vm",
    "resume_vm",
    # Hyper-V Tools (individual tools disabled - using portmanteau)
    "VMState",
    "VMSize",
    "VMDisk",
    "VMSnapshot",
    "VMNetworkAdapter",
    "VirtualMachine",
    # "list_hyperv_vms",  # Disabled - use hyperv_management portmanteau tool
    # "get_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "start_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
    # "stop_hyperv_vm",  # Disabled - use hyperv_management portmanteau tool
]
