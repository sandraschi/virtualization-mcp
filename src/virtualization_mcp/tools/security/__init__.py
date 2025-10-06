"""
Security Tools for virtualization-mcp

This module provides security-related tools for virtual machine management,
including AI-powered security analysis, malware detection, and security testing.
"""

# AI Security Tools
from virtualization_mcp.tools.security.ai_security_tools import (
    TestSeverity as SecurityThreatLevel,
    SecurityFinding,
    SecurityReport,
    start_security_scan,
    get_security_scan_status
)

# Malware Analysis Tools
from virtualization_mcp.tools.security.malware_tools import (
    AnalysisStatus,
    ThreatLevel,
    Detection,
    AnalysisResult,
    analyze_file,
    get_analysis,
    list_analyses,
    delete_analysis,
    list_quarantine
)

# Security Testing Tools
from virtualization_mcp.tools.security.security_testing_tools import (
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

__all__ = [
    # AI Security Tools
    'SecurityThreatLevel',  # Alias for backward compatibility
    'TestSeverity',
    'SecurityFinding',
    'SecurityReport',  # Alias for backward compatibility
    'SecurityTestResult',
    'start_security_scan',  # Alias for backward compatibility
    'run_security_scan',
    'get_security_scan_status',
    
    # Malware Analysis Tools
    'AnalysisStatus',
    'ThreatLevel',
    'Detection',
    'AnalysisResult',
    'analyze_file',
    'get_analysis',
    'list_analyses',
    'delete_analysis',
    'list_quarantine',
    
    # Security Testing Tools
    'TestStatus',
    'TestSeverity',
    'SecurityTestResult',
    'SecurityTester',
    'security_tester',
    'run_security_scan',
    'get_test_status',
    'cancel_test',
    'list_available_tools',
    'generate_report'
]



