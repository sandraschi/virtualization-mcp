# Sandbox assets (reuse folder)

Store the Windows Sandbox full-dev installer files here so you don’t re-download them every time.

**Place these files in this folder** (from [winget-cli Releases](https://github.com/microsoft/winget-cli/releases) → Assets):

- `DesktopAppInstaller_Dependencies.zip` (~93 MB)
- `Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle` (~206 MB)

They are gitignored. Then in the webapp **Full dev setup**, set **Assets folder** to this path, e.g.:

- `D:\Dev\repos\virtualization-mcp\assets\sandbox`

The setup script is written here when you click **Launch with full dev setup**; the sandbox maps this folder to `C:\Assets` and runs the script at logon.
