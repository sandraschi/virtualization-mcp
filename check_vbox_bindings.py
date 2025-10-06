#!/usr/bin/env python3
"""
Check VirtualBox Python bindings installation and import status.
"""
import os
import site
import sys
from pathlib import Path


def print_section(title):
    """Print a section header."""
    separator = '-' * 80
    print(f"\n{separator}\n{title}\n{separator}")


def check_python_environment():
    """Print Python environment information."""
    print_section("Python Environment")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("\nPython path:")
    for i, path in enumerate(sys.path, 1):
        print(f"  {i}. {path}")


def check_site_packages():
    """Check site packages and look for VirtualBox bindings."""
    print_section("Site Packages")
    
    # Get all site packages directories
    site_packages = site.getsitepackages()
    user_site = site.getusersitepackages()
    
    print("System site packages:")
    for i, path in enumerate(site_packages, 1):
        print(f"  {i}. {path}")
    print(f"\nUser site packages: {user_site}")
    
    # Look for vboxapi or virtualbox in site packages
    print_section("Searching for VirtualBox Python Bindings")
    
    # Check standard locations
    search_paths = [
        *site_packages,
        user_site,
        r"C:\Program Files\Oracle\VirtualBox\sdk\installer\python",
        r"C:\Program Files\Oracle\VirtualBox\sdk\bindings\python"
    ]
    
    found = False
    for path in search_paths:
        path = Path(path)
        if not path.exists():
            continue
            
        # Look for vboxapi or virtualbox directories
        for item in path.iterdir():
            if item.is_dir() and 'vboxapi' in item.name.lower():
                print(f"\nFound vboxapi at: {item}")
                found = True
                
                # Try to import it
                try:
                    sys.path.insert(0, str(item.parent))
                    import vboxapi  # pylint: disable=import-outside-toplevel
                    print("  ✓ Successfully imported vboxapi!")
                    print(f"  Location: {vboxapi.__file__}")
                    
                    # Try to create VirtualBox manager
                    try:
                        mgr = vboxapi.VirtualBoxManager(None, None)
                        vbox = mgr.getVirtualBox()
                        print(f"  ✓ VirtualBox version: {vbox.version}")
                    except Exception as e:  # pylint: disable=broad-except
                        print(f"  ✗ Failed to create VirtualBox manager: {e}")
                        
                except Exception as e:  # pylint: disable=broad-except
                    print(f"  ✗ Failed to import vboxapi: {e}")
                    
            # Also check for virtualbox module
            if item.is_dir() and item.name.lower() == 'virtualbox':
                print(f"\nFound virtualbox module at: {item}")
                found = True
                
                # Try to import it
                try:
                    sys.path.insert(0, str(item.parent))
                    import virtualbox  # pylint: disable=import-outside-toplevel
                    print("  ✓ Successfully imported virtualbox!")
                    print(f"  Location: {virtualbox.__file__}")
                    
                    # Try to connect to VirtualBox
                    try:
                        vbox = virtualbox.VirtualBox()
                        print(f"  ✓ VirtualBox version: {vbox.version}")
                    except Exception as e:  # pylint: disable=broad-except
                        print(f"  ✗ Failed to connect to VirtualBox: {e}")
                        
                except Exception as e:  # pylint: disable=broad-except
                    print(f"  ✗ Failed to import virtualbox: {e}")
    
    if not found:
        print("No VirtualBox Python bindings found in standard locations.")


def check_virtualbox_installation():
    """Check if VirtualBox is installed and accessible."""
    print_section("VirtualBox Installation")
    
    # Check if VirtualBox is in PATH
    vboxmanage = "VBoxManage" if os.name == 'nt' else "vboxmanage"
    vbox_path = None
    
    for path in os.environ["PATH"].split(os.pathsep):
        exe = os.path.join(path, f"{vboxmanage}.exe")
        if os.path.isfile(exe):
            vbox_path = exe
            break
    
    if vbox_path:
        print(f"Found VBoxManage at: {vbox_path}")
        
        # Try to get version
        try:
            import subprocess  # pylint: disable=import-outside-toplevel
            result = subprocess.run(
                [vbox_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"VirtualBox version: {result.stdout.strip()}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Failed to get VirtualBox version: {e}")
    else:
        print("VBoxManage not found in PATH. Is VirtualBox installed?")


def main():
    """Main function."""
    print("VirtualBox Python Bindings Checker")
    print("=" * 80)
    
    check_python_environment()
    check_site_packages()
    check_virtualbox_installation()
    
    print_section("Summary")
    print("Use this information to diagnose VirtualBox Python bindings installation.")


if __name__ == "__main__":
    main()



