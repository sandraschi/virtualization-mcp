"""Tests for VBoxManager compat_adapter utilities (validate_vm_name, log_path)."""

from unittest.mock import patch

import pytest

from virtualization_mcp.vbox.compat_adapter import VBoxManager, VBoxManagerError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    """Return a VBoxManager instance with VBoxManage mocked to avoid real CLI calls."""
    with (
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManage") as mock_cls,
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._validate_vboxmanage"),
    ):
        mock_cls.return_value.version = "7.2.6"
        yield VBoxManager()


# ---------------------------------------------------------------------------
# validate_vm_name
# ---------------------------------------------------------------------------


class TestValidateVmName:
    """VBoxManager.validate_vm_name — pure boolean logic, no subprocess."""

    def test_valid_simple(self, manager):
        assert manager.validate_vm_name("MyVM") is True

    def test_valid_with_hyphen(self, manager):
        assert manager.validate_vm_name("my-test-vm") is True

    def test_valid_with_underscore(self, manager):
        assert manager.validate_vm_name("my_test_vm") is True

    def test_valid_with_numbers(self, manager):
        assert manager.validate_vm_name("vm42") is True

    def test_valid_mixed_case(self, manager):
        assert manager.validate_vm_name("Ubuntu-22.04_LTS") is True

    # --- invalid ---

    def test_invalid_empty(self, manager):
        assert manager.validate_vm_name("") is False

    def test_invalid_whitespace(self, manager):
        assert manager.validate_vm_name("   ") is False

    def test_invalid_slash(self, manager):
        assert manager.validate_vm_name("my/vm") is False

    def test_invalid_backslash(self, manager):
        assert manager.validate_vm_name("my\\vm") is False

    def test_invalid_colon(self, manager):
        assert manager.validate_vm_name("my:vm") is False

    def test_invalid_asterisk(self, manager):
        assert manager.validate_vm_name("my*vm") is False

    def test_invalid_question_mark(self, manager):
        assert manager.validate_vm_name("my?vm") is False

    def test_invalid_quotes(self, manager):
        assert manager.validate_vm_name('my"vm') is False

    def test_invalid_angle_brackets(self, manager):
        assert manager.validate_vm_name("<myvm>") is False

    def test_invalid_pipe(self, manager):
        assert manager.validate_vm_name("my|vm") is False

    def test_invalid_none(self, manager):
        assert manager.validate_vm_name(None) is False


# ---------------------------------------------------------------------------
# log_path
# ---------------------------------------------------------------------------


class TestLogPath:
    """VBoxManager.log_path property — resolves to an existing directory."""

    def test_returns_string(self, manager):
        path = manager.log_path
        assert isinstance(path, str)
        assert len(path) > 0

    @patch("os.path.isdir", return_value=True)
    @patch("os.path.expanduser", return_value="/home/user")
    def test_returns_first_existing(self, mock_user, mock_isdir, manager):
        path = manager.log_path
        assert "VirtualBox" in path
        assert "Logs" in path

    @patch("os.path.isdir", return_value=False)
    @patch("os.path.expanduser", return_value="/home/user")
    def test_returns_first_candidate_when_none_exist(self, mock_user, mock_isdir, manager):
        path = manager.log_path
        assert "VirtualBox" in path
        assert "Logs" in path


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------


class TestRunCommand:
    """VBoxManager.run_command — delegates to _execute, returns dict."""

    def test_run_command_returns_dict(self, manager):
        result = manager.run_command(["list", "vms"])
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["command"] == ["VBoxManage", "list", "vms"]

    def test_run_command_with_capture_json(self, manager):
        result = manager.run_command(["list", "vms"], capture_json=True)
        assert result["success"] is True
        assert "output" in result

    def test_run_command_raises_on_failure(self, manager):
        with patch.object(manager, "_execute", side_effect=VBoxManagerError("boom")):
            import pytest

            with pytest.raises(VBoxManagerError):
                manager.run_command(["bad", "cmd"])


# ---------------------------------------------------------------------------
# VBoxManager construction
# ---------------------------------------------------------------------------


class TestVBoxManagerInit:
    """VBoxManager constructor edge cases."""

    def test_init_with_custom_path(self):
        with (
            patch("virtualization_mcp.vbox.compat_adapter.VBoxManage") as mock_cls,
            patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._validate_vboxmanage"),
        ):
            mock_cls.return_value.version = "7.2.6"
            m = VBoxManager("C:\\custom\\VBoxManage.exe")
            assert m.vboxmanage_path == "C:\\custom\\VBoxManage.exe"
