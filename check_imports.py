"""
Script to check for import errors in Python files.

This script will:
1. Find all Python files in the project
2. Attempt to import each module
3. Report any import errors
"""

import ast
import importlib
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the given directory."""
    return list(directory.rglob("*.py"))

def get_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError as e:
            print(f"\nSyntax error in {file_path}: {e}")
            return set()
    
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split('.')[0])  # Only get the base module name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])  # Only get the base module name
    
    return imports

def check_imports() -> Dict[str, List[str]]:
    """Check all Python files for import errors."""
    python_files = find_python_files(PROJECT_ROOT / "src" / "virtualization-mcp")
    errors = {}
    
    for file_path in python_files:
        # Skip __pycache__ and virtual environment directories
        if any(part.startswith('__pycache__') or part.startswith('.') for part in file_path.parts):
            continue
            
        print(f"Checking {file_path.relative_to(PROJECT_ROOT)}...", end='\r')
        
        # Get the module path (e.g., virtualization-mcp.plugins.network_analyzer)
        rel_path = file_path.relative_to(PROJECT_ROOT / "src")
        module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
        
        # Skip __init__.py files for now as they might have side effects
        if file_path.name == "__init__.py":
            continue
        
        try:
            # Try to import the module
            importlib.import_module(module_path)
        except ImportError as e:
            module_name = e.name if hasattr(e, 'name') else 'unknown'
            if module_name not in errors:
                errors[module_name] = []
            errors[module_name].append(f"{file_path.relative_to(PROJECT_ROOT)}: {str(e)}")
        except Exception as e:
            error_type = type(e).__name__
            if error_type not in errors:
                errors[error_type] = []
            errors[error_type].append(f"{file_path.relative_to(PROJECT_ROOT)}: {str(e)}")
    
    return errors

def main():
    print("Checking for import errors...\n")
    
    # First, check for syntax errors and missing imports
    errors = check_imports()
    
    print("\n" + "="*80)
    print("IMPORT CHECK RESULTS")
    print("="*80)
    
    if not errors:
        print("\nNo import errors found!")
        return
    
    # Group errors by module
    for module, error_msgs in errors.items():
        print(f"\n{module}:")
        for msg in error_msgs:
            print(f"  - {msg}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Found {len(errors)} unique error types across {sum(len(msgs) for msgs in errors.values())} files.")
    
    # Suggest fixes for common issues
    if 'ModuleNotFoundError' in errors:
        print("\nCommon fixes for ModuleNotFoundError:")
        print("1. Check if the module is installed (pip install <module>)")
        print("2. Check for typos in the import statement")
        print("3. Check if the module is in your PYTHONPATH")
        print("4. For local modules, check the file structure and __init__.py files")

if __name__ == "__main__":
    main()
