"""Tests for vbox_compat _parse_vm_list fixes."""

from virtualization_mcp.vbox_compat import VBoxManage


def test_strips_uuid_annotation_from_name():
    """VM name with (UUID: ...) * annotation should be cleaned."""
    vm = VBoxManage()
    output = '"fresh-install (UUID: c9876aac-0d4c-49df-8c02-89cc1bb5748e) *" {c9876aac-0d4c-49df-8c02-89cc1bb5748e}'
    parsed = vm._parse_vm_list(output)
    assert parsed[0]["name"] == "fresh-install", f"Got: {parsed[0]['name']}"


def test_blank_line_separates_vms():
    """Blank lines between VM blocks should produce separate VM entries."""
    vm = VBoxManage()
    output = '"vm1" {uuid1-xxx}\nName: vm1\nState: running\n\n"vm2" {uuid2-yyy}\nName: vm2\nState: stopped'
    parsed = vm._parse_vm_list(output, verbose=True)
    assert len(parsed) == 2, f"Expected 2 VMs, got {len(parsed)}"


def test_short_format_multi_vm():
    """Multiple VMs in short format should all be parsed."""
    vm = VBoxManage()
    output = '"my-vm" {abc}\n"another-vm" {def}'
    parsed = vm._parse_vm_list(output)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "my-vm"
    assert parsed[1]["name"] == "another-vm"


def test_annotation_regex_variants():
    """Different annotation formats should all be stripped."""
    vm = VBoxManage()
    cases = [
        ('"test-vm (UUID: abc-123) *" {abc}', "test-vm"),
        ('"test-vm (UUID: abc-123)" {abc}', "test-vm"),
        ('"test-vm *" {abc}', "test-vm *"),  # no UUID prefix, not stripped
        ('"plain-vm" {uuid}', "plain-vm"),
    ]
    for raw, expected in cases:
        parsed = vm._parse_vm_list(raw)
        assert parsed[0]["name"] == expected, f"For {raw!r}: expected {expected!r}, got {parsed[0]['name']!r}"
