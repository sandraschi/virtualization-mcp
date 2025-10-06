"""
virtualization-mcp Tools Package

This package contains all the tools for virtualization-mcp organized into logical modules.
"""

# Import the registration function
from virtualization_mcp.tools.register_tools import register_all_tools

# Import VM tools
from virtualization_mcp.tools.vm.vm_tools import (
    list_vms,
    get_vm_info,
    start_vm,
    stop_vm,
    create_vm,
    delete_vm,
    clone_vm,
    modify_vm,
    pause_vm,
    resume_vm,
    reset_vm
)

# Import tool modules
from virtualization_mcp.tools.example_tools import (
    greet,
    create_task,
    list_tasks,
    get_counter,
    analyze_file
)

# Import sandbox tools
from virtualization_mcp.tools.dev.sandbox_tools import (
    SandboxType,
    TestResult,
    create_sandbox,
    run_in_sandbox,
    cleanup_sandbox
)
# Import security tools
from virtualization_mcp.tools.security import (
    # AI Security Tools
    SecurityThreatLevel,  # Backward compatibility
    TestSeverity,
    SecurityFinding,
    SecurityReport,  # Backward compatibility
    SecurityTestResult,
    start_security_scan,  # Backward compatibility
    run_security_scan,
    get_security_scan_status,
    
    # Malware Analysis Tools
    AnalysisStatus,
    ThreatLevel,
    Detection,
    AnalysisResult,
    analyze_file,
    get_analysis,
    list_analyses,
    delete_analysis,
    list_quarantine,
    
    # Security Testing Tools
    TestStatus,
    TestSeverity,
    SecurityTestResult,
    SecurityTester,
    security_tester,
    run_security_scan,
    get_test_status,
    cancel_test,
    list_available_tools,
    generate_report
)

# Import system tools
from virtualization_mcp.tools.system import (
    create_backup,
    list_backups,
    delete_backup
)

# Import development tools
from virtualization_mcp.tools.dev import (
    document_tool,
    get_api_documentation,
    get_openapi_schema,
    ParameterDocumentation,
    ToolDocumentation
)

# Import monitoring tools
from virtualization_mcp.tools.monitoring import (
    MetricsManager,
    metrics_manager,
    start_metrics_server,
    record_api_request,
    record_error,
    update_vm_metrics,
    update_system_metrics,
    get_metrics
)

# Import network tools
from virtualization_mcp.tools.network import (
    # Network Configuration
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
    remove_hostonly_network,
    
    # Network Analyzer
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

# Import VM tools
from virtualization_mcp.tools.vm import (
    # Base VM tools
    list_vms, get_vm_info, start_vm, stop_vm, create_vm, delete_vm,
    clone_vm, modify_vm, reset_vm, pause_vm, resume_vm,
    
    # Hyper-V tools
    VMState, VMSize, VMDisk, VMSnapshot, VMNetworkAdapter, VirtualMachine,
    list_hyperv_vms, get_hyperv_vm, start_hyperv_vm, stop_hyperv_vm
)

# Re-export the registration functions and tools
__all__ = [
    'register_all_tools',
    
    # VM Tools
    'list_vms',
    'get_vm_info',
    'start_vm',
    'stop_vm',
    'create_vm',
    'delete_vm',
    'clone_vm',
    'modify_vm',
    'pause_vm',
    'resume_vm',
    'reset_vm',
    
    # Example Tools
    'greet',
    'create_task',
    'list_tasks',
    'get_counter',
    'analyze_file',
    
    # Security Tools
    'SecurityThreatLevel',  # Backward compatibility
    'TestSeverity',
    'SecurityFinding',
    'SecurityReport',  # Backward compatibility
    'SecurityTestResult',
    'start_security_scan',  # Backward compatibility
    'run_security_scan',
    'get_security_scan_status',
    'AnalysisStatus',
    'ThreatLevel',
    'Detection',
    'AnalysisResult',
    'analyze_file',
    'get_analysis',
    'list_analyses',
    'delete_analysis',
    'list_quarantine',
    'TestStatus',
    'TestSeverity',
    'SecurityTestResult',
    'SecurityTester',
    'security_tester',
    'run_security_scan',
    'get_test_status',
    'cancel_test',
    'list_available_tools',
    'generate_report',
    
    # System Tools
    'create_backup',
    'list_backups',
    'delete_backup',
    
    # Development Tools
    'document_tool',
    'get_api_documentation',
    'get_openapi_schema',
    'ParameterDocumentation',
    'ToolDocumentation',
    
    # Monitoring Tools
    'MetricsManager',
    'metrics_manager',
    'start_metrics_server',
    'record_api_request',
    'record_error',
    'update_vm_metrics',
    'update_system_metrics',
    'get_metrics',
    
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
    'unregister_websocket',
    
    # VM Tools
    'list_vms',
    'get_vm_info',
    'start_vm',
    'stop_vm',
    'create_vm',
    'delete_vm',
    'clone_vm',
    'modify_vm',
    'reset_vm',
    'pause_vm',
    'resume_vm',
    
    # Hyper-V Tools
    'VMState',
    'VMSize',
    'VMDisk',
    'VMSnapshot',
    'VMNetworkAdapter',
    'VirtualMachine',
    'list_hyperv_vms',
    'get_hyperv_vm',
    'start_hyperv_vm',
    'stop_hyperv_vm'
]



