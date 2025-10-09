#!/usr/bin/env python3
"""
GLAMA Gold Standard Test Runner

Runs comprehensive tests to validate progress toward GLAMA Gold Standard (80%+ coverage).
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=False
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def check_coverage():
    """Check current test coverage."""
    print("🔍 Checking current test coverage...")
    
    # Run coverage analysis
    result = run_command(
        "python -m pytest --cov=src/virtualization_mcp --cov-report=json --cov-report=term-missing -q"
    )
    
    if result["success"]:
        print("✅ Coverage analysis completed")
        print(result["stdout"])
        
        # Try to parse coverage JSON
        try:
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
                total_coverage = coverage_data["totals"]["percent_covered"]
                print(f"📊 Current Coverage: {total_coverage:.1f}%")
                
                # Check if we meet Gold Standard
                if total_coverage >= 80.0:
                    print("🏆 GLAMA GOLD STANDARD ACHIEVED!")
                    return True
                else:
                    gap = 80.0 - total_coverage
                    print(f"🎯 Need {gap:.1f}% more coverage for Gold Standard")
                    return False
        except FileNotFoundError:
            print("⚠️  Coverage JSON file not found")
            return False
    else:
        print("❌ Coverage analysis failed")
        print(result["stderr"])
        return False

def run_portmanteau_tests():
    """Run portmanteau tool tests."""
    print("🧪 Running portmanteau tool tests...")
    
    test_files = [
        "tests/test_portmanteau_vm_management.py",
        "tests/test_portmanteau_network_management.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  Running {test_file}...")
            result = run_command(f"python -m pytest {test_file} -v")
            if result["success"]:
                print(f"  ✅ {test_file} passed")
            else:
                print(f"  ❌ {test_file} failed")
                print(f"     {result['stderr']}")
        else:
            print(f"  ⚠️  {test_file} not found")

def validate_gold_standard():
    """Validate GLAMA Gold Standard requirements."""
    print("🏆 Validating GLAMA Gold Standard requirements...")
    
    requirements = {
        "Test Coverage": False,
        "Security Scanning": False,
        "Documentation": False,
        "CI/CD Pipeline": False,
        "Performance": False
    }
    
    # Check test coverage
    coverage_result = check_coverage()
    requirements["Test Coverage"] = coverage_result
    
    # Check security scanning
    print("🔒 Checking security scanning...")
    security_result = run_command("python -m bandit -r src/virtualization_mcp -f json")
    if security_result["success"]:
        requirements["Security Scanning"] = True
        print("  ✅ Security scanning configured")
    else:
        print("  ❌ Security scanning not configured")
    
    # Check documentation
    print("📚 Checking documentation...")
    if os.path.exists("README.md") and os.path.exists("docs/"):
        requirements["Documentation"] = True
        print("  ✅ Documentation present")
    else:
        print("  ❌ Documentation incomplete")
    
    # Check CI/CD
    print("🔄 Checking CI/CD pipeline...")
    if os.path.exists(".github/workflows/"):
        requirements["CI/CD Pipeline"] = True
        print("  ✅ CI/CD pipeline configured")
    else:
        print("  ❌ CI/CD pipeline missing")
    
    # Summary
    print("\n📋 GLAMA Gold Standard Status:")
    for req, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {req}")
    
    gold_standard_met = all(requirements.values())
    if gold_standard_met:
        print("\n🏆 GLAMA GOLD STANDARD ACHIEVED!")
    else:
        print("\n🎯 Working toward GLAMA Gold Standard...")
    
    return gold_standard_met

def main():
    """Main test runner."""
    print("🚀 GLAMA Gold Standard Test Runner")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run portmanteau tests
    run_portmanteau_tests()
    
    # Validate Gold Standard
    gold_standard = validate_gold_standard()
    
    # Final status
    print("\n" + "=" * 50)
    if gold_standard:
        print("🎉 CONGRATULATIONS! GLAMA Gold Standard achieved!")
        sys.exit(0)
    else:
        print("📈 Progress toward GLAMA Gold Standard...")
        print("   Continue implementing the 4-week plan")
        sys.exit(1)

if __name__ == "__main__":
    main()

