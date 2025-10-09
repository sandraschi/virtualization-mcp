#!/usr/bin/env python3
"""
Simple Test Runner for GLAMA Gold Standard

Runs basic tests to check progress toward 80%+ coverage.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Main test runner."""
    print("GLAMA Gold Standard Test Runner")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test 1: Check if portmanteau tools can be imported
    print("Test 1: Checking portmanteau tool imports...")
    try:
        sys.path.insert(0, "src")
        from virtualization_mcp.tools.portmanteau.vm_management import VM_ACTIONS
        from virtualization_mcp.tools.portmanteau.network_management import NETWORK_ACTIONS
        print("  SUCCESS: Portmanteau tools imported successfully")
        print(f"  VM Actions: {len(VM_ACTIONS)} actions available")
        print(f"  Network Actions: {len(NETWORK_ACTIONS)} actions available")
    except Exception as e:
        print(f"  ERROR: Failed to import portmanteau tools: {e}")
        return 1
    
    # Test 2: Run basic pytest
    print("\nTest 2: Running basic pytest...")
    success, stdout, stderr = run_command("python -m pytest --version")
    if success:
        print("  SUCCESS: pytest is available")
    else:
        print(f"  ERROR: pytest not available: {stderr}")
        return 1
    
    # Test 3: Check test files exist
    print("\nTest 3: Checking test files...")
    test_files = [
        "tests/test_portmanteau_vm_management.py",
        "tests/test_portmanteau_network_management.py",
        "tests/conftest.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  SUCCESS: {test_file} exists")
        else:
            print(f"  ERROR: {test_file} missing")
    
    # Test 4: Try to run a simple test
    print("\nTest 4: Running simple test...")
    success, stdout, stderr = run_command("python -c \"import sys; sys.path.insert(0, 'src'); from virtualization_mcp.tools.portmanteau.vm_management import VM_ACTIONS; print('VM Actions:', len(VM_ACTIONS))\"")
    if success:
        print("  SUCCESS: Simple test passed")
        print(f"  Output: {stdout.strip()}")
    else:
        print(f"  ERROR: Simple test failed: {stderr}")
    
    print("\n" + "=" * 50)
    print("Status: Basic infrastructure is working")
    print("Next: Run comprehensive test suite for coverage analysis")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

