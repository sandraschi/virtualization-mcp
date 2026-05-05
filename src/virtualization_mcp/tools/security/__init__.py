"""
Security Tools for virtualization-mcp

This module provides security-related tools for virtual machine management,
including AI-powered security analysis, malware detection, and security testing.
"""

# AI Security Tools
from virtualization_mcp.tools.security.ai_security_tools import (
    SecurityFinding,
    SecurityReport,
    get_security_scan_status,
    start_security_scan,
)
from virtualization_mcp.tools.security.ai_security_tools import (
    TestSeverity as SecurityThreatLevel,
)

# Malware Analysis Tools
from virtualization_mcp.tools.security.malware_tools import (
    AnalysisResult,
    AnalysisStatus,
    Detection,
    ThreatLevel,
    analyze_file,
    delete_analysis,
    get_analysis,
    list_analyses,
    list_quarantine,
)

# Security Testing Tools
from virtualization_mcp.tools.security.security_testing_tools import (
    SecurityTester,
    SecurityTestResult,
    TestSeverity,
    TestStatus,
    cancel_test,
    generate_report,
    get_test_status,
    list_available_tools,
    run_security_scan,
    security_tester,
)

__all__ = [
    "AnalysisResult",
    # Malware Analysis Tools
    "AnalysisStatus",
    "Detection",
    "SecurityFinding",
    "SecurityReport",  # Alias for backward compatibility
    "SecurityTestResult",
    "SecurityTestResult",
    "SecurityTester",
    # AI Security Tools
    "SecurityThreatLevel",  # Alias for backward compatibility
    "TestSeverity",
    "TestSeverity",
    # Security Testing Tools
    "TestStatus",
    "ThreatLevel",
    "analyze_file",
    "cancel_test",
    "delete_analysis",
    "generate_report",
    "get_analysis",
    "get_security_scan_status",
    "get_test_status",
    "list_analyses",
    "list_available_tools",
    "list_quarantine",
    "run_security_scan",
    "run_security_scan",
    "security_tester",
    "start_security_scan",  # Alias for backward compatibility
]
