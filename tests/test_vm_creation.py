"""
Test VM creation with the compatibility adapter.
"""
import unittest
from virtualization_mcp.vbox.compat_adapter import VBoxManager

class TestVMCreation(unittest.TestCase):    
    def setUp(self):
        """Set up the test environment."""
        self.manager = VBoxManager()
        self.test_vm_name = "test-vm-creation"
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up test VM if it exists
        try:
            if self.manager.vm_exists(self.test_vm_name):
                self.manager.delete_vm(self.test_vm_name, delete_disks=True)
        except Exception as e:
            print(f"Warning: Failed to clean up test VM: {e}")
    
    def test_create_vm_positional_args(self):
        """Test VM creation with positional arguments."""
        # Create VM with positional arguments
        vm_info = self.manager.create_vm(
            self.test_vm_name,  # name
            "Linux_64",        # ostype
            2048,              # memory in MB
            2                  # cpus
        )
        
        # Verify VM was created
        self.assertEqual(vm_info["name"], self.test_vm_name)
        self.assertEqual(vm_info["ostype"], "Linux_64")
        self.assertEqual(vm_info["memory"], 2048)
        self.assertEqual(vm_info["cpus"], 2)
        
        # Verify VM exists
        self.assertTrue(self.manager.vm_exists(self.test_vm_name))
    
    def test_create_vm_named_args(self):
        """Test VM creation with named arguments."""
        # Create VM with named arguments
        vm_info = self.manager.create_vm(
            name=self.test_vm_name,
            ostype="Linux_64",
            memory=2048,
            cpus=2,
            vram_mb=128,
            disk_size_mb=32768
        )
        
        # Verify VM was created with correct parameters
        self.assertEqual(vm_info["name"], self.test_vm_name)
        self.assertEqual(vm_info["ostype"], "Linux_64")
        self.assertEqual(vm_info["memory"], 2048)
        self.assertEqual(vm_info["cpus"], 2)
        self.assertEqual(vm_info["vram"], 128)
        
        # Verify VM exists
        self.assertTrue(self.manager.vm_exists(self.test_vm_name))

if __name__ == "__main__":
    unittest.main()



