# VirtualBox VM assets (reuse folder)

Store VM installation media and ready-to-use appliances here.

**Place files such as:**

- **ISOs**: e.g. `ubuntu-24.04-desktop-amd64.iso`, `Win11_23H2_English_x64v2.iso`
- **OVA/OVF**: exported appliances, e.g. `win11pro.ova` (installed and ready to use)

They are gitignored. In the webapp: **Create New VM** and **Attach ISO** use this folder (dropdown lists files here).

---

## Win 11 Pro VM – installed and ready to use

To have a **Windows 11 Pro VM as a reusable asset** (install once, then import whenever you need it):

### One-time setup

1. **Get the Windows 11 Pro ISO**  
   Download from Microsoft (e.g. [Create Windows 11 installation media](https://www.microsoft.com/software-download/windows11)) and put the ISO in this folder, e.g. `assets/vbox/Win11_23H2_English_x64v2.iso`.

2. **Create a VM from the webapp**  
   - Open **VirtualBox** in the webapp → **Create New VM**  
   - Name: e.g. `win11-pro-install`  
   - Template: **Win 11 Pro**  
   - ISO: select your Windows 11 ISO from the dropdown  
   - Create  

3. **Install Windows**  
   - Start the VM, complete the Windows 11 install (license and setup as usual).  
   - Optionally install tools (e.g. Guest Additions, browser, dev tools), then shut down the VM.

4. **Export as OVA**  
   - In VirtualBox (or via VBoxManage): **File → Export Appliance** (or `VBoxManage export win11-pro-install -o path\to\win11pro.ova`).  
   - Save the OVA into this folder, e.g. `assets/vbox/win11pro.ova`.  
   - You can delete the temporary VM `win11-pro-install` if you no longer need it.

### Reuse (ready-to-use VM)

- **File → Import Appliance** in VirtualBox (or `VBoxManage import assets/vbox/win11pro.ova`) and choose a name for the new VM.  
- Start the VM – Windows 11 Pro is already installed and ready to use.  
- Repeat import whenever you need a fresh copy; the OVA stays in `assets/vbox` as your master asset.
