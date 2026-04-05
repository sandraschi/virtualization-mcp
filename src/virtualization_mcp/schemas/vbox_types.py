"""VirtualBox-related type aliases for MCP tool schemas (enums / common literals)."""

from typing import Literal

# Common VirtualBox --ostype IDs (subset). Full list: system_management(action="ostypes") or VBoxManage list ostypes.
VBoxGuestOSType = Literal[
    "Other",
    "Other_64",
    "Ubuntu_64",
    "Ubuntu22_64",
    "Debian_64",
    "Fedora_64",
    "ArchLinux_64",
    "Windows10_64",
    "Windows11_64",
    "Windows2019_64",
    "Windows2022_64",
    "MacOS_64",
    "Oracle_64",
    "OpenSUSE_Leap_64",
    "RedHat_64",
    "Gentoo_64",
]

STORAGE_CONTROLLER_TYPE = Literal["ide", "sata", "scsi", "sas", "usb", "pcie"]

NIC_MODE = Literal["none", "null", "nat", "bridged", "intnet", "hostonly", "generic"]
