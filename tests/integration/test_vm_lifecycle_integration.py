"""
Integration tests for complete VM lifecycle workflows.

Tests end-to-end scenarios combining multiple operations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.integration
class TestVMLifecycleIntegration:
    """Integration tests for VM lifecycle."""
    
    @pytest.mark.asyncio
    async def test_create_start_stop_delete_workflow(self):
        """Test complete VM lifecycle: create → start → stop → delete."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="success")
            
            from virtualization_mcp.vbox.compat_adapter import VBoxManager
            manager = VBoxManager()
            
            # Create VM
            result = manager.create_vm(name="test-vm", ostype="Linux_64", memory=2048, cpus=2)
            assert result is not None
            
            # Start VM
            result = manager.start_vm("test-vm")
            assert result is not None
            
            # Stop VM
            result = manager.stop_vm("test-vm")
            assert result is not None
            
            # Delete VM
            result = manager.delete_vm("test-vm")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_snapshot_workflow(self):
        """Test snapshot workflow: create → restore → delete."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="success")
            
            from virtualization_mcp.vbox.compat_adapter import VBoxManager
            manager = VBoxManager()
            
            # Create snapshot
            result = manager.create_snapshot("test-vm", "snap1", "Test snapshot")
            assert result is not None
            
            # Restore snapshot  
            result = manager.restore_snapshot("test-vm", "snap1")
            assert result is not None
            
            # Delete snapshot
            result = manager.delete_snapshot("test-vm", "snap1")
            assert result is not None


@pytest.mark.integration
class TestPortmanteauIntegration:
    """Integration tests for portmanteau tools."""
    
    @pytest.mark.asyncio
    async def test_vm_management_full_workflow(self):
        """Test VM management portmanteau handles full workflow."""
        from virtualization_mcp.tools.portmanteau.vm_management import register_vm_management_tool
        
        mock_mcp = MagicMock()
        captured_func = None
        
        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal captured_func
                captured_func = func
                return func
            return decorator
        
        mock_mcp.tool = capture_tool
        register_vm_management_tool(mock_mcp)
        
        # Test workflow: list → create → start → info → stop → delete
        with patch('virtualization_mcp.tools.portmanteau.vm_management.list_vms', new_callable=AsyncMock) as m1:
            with patch('virtualization_mcp.tools.portmanteau.vm_management.create_vm', new_callable=AsyncMock) as m2:
                with patch('virtualization_mcp.tools.portmanteau.vm_management.start_vm', new_callable=AsyncMock) as m3:
                    with patch('virtualization_mcp.tools.portmanteau.vm_management.get_vm_info', new_callable=AsyncMock) as m4:
                        with patch('virtualization_mcp.tools.portmanteau.vm_management.stop_vm', new_callable=AsyncMock) as m5:
                            with patch('virtualization_mcp.tools.portmanteau.vm_management.delete_vm', new_callable=AsyncMock) as m6:
                                m1.return_value = {"vms": []}
                                m2.return_value = {"success": True}
                                m3.return_value = {"success": True}
                                m4.return_value = {"name": "test"}
                                m5.return_value = {"success": True}
                                m6.return_value = {"success": True}
                                
                                # Execute workflow
                                await captured_func(action="list")
                                await captured_func(action="create", vm_name="test", os_type="Linux_64", memory_mb=2048, disk_size_gb=20)
                                await captured_func(action="start", vm_name="test")
                                await captured_func(action="info", vm_name="test")
                                await captured_func(action="stop", vm_name="test")
                                await captured_func(action="delete", vm_name="test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

