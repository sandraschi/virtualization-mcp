# Windows Sandbox

## What it is

Windows Sandbox is a lightweight, disposable VM built into Windows. It creates an isolated environment that's destroyed when you close it. Perfect for testing installs, running untrusted code, or provisioning a fresh dev environment in seconds.

## Requirements

- **Windows 11 Pro/Enterprise/Education**
- **Sandbox feature enabled**

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -All
```

## Launching a sandbox

From the **Sandbox** page:

| Mode | Purpose |
|------|---------|
| **Consumer (nearly naked)** | INSTALL.md validation — winget only, no dev stack; optional Claude MSIX |
| **Dev Infra** | Online dev stack (git, node, python, ruff, just, biome) |
| **Full Dev** | Offline/selectable full tool list |

Or from the host:

```powershell
.\scripts\Launch-ConsumerSandbox.ps1 -InstallClaudeDesktop
.\scripts\Launch-DevInfraSandbox.ps1
```

## Dev setup options (Dev Infra / Full Dev only)

Not installed in **Consumer** mode — that mode is for end-user install doc testing.

| Tool | Package |
|------|---------|
| Python 3.12 | winget: `Python.Python.3.12` |
| Git | winget: `Git.Git` |
| Node.js LTS | winget: `OpenJS.NodeJS.LTS` |
| VS Code | winget: `Microsoft.VisualStudioCode` |
| uv | winget: `astral-sh.uv` |
| Just | winget: `Casey.Just` |
| Windsurf | winget: `Codeium.Windsurf` |
| Cursor | winget: `Anysphere.Cursor` |
| Antigravity | winget: `Google.Antigravity` |
| Claude Desktop | MSIX download + `Add-AppxPackage` |

## Host Ollama

Toggle "Use host Ollama" to set `OLLAMA_HOST` inside the sandbox pointing to your host machine's Ollama instance. The sandbox detects the host gateway automatically.

## Airgap mode

Enable airgap to disable networking inside the sandbox. Useful for:
- Running sensitive code with zero egress
- Testing installs in complete isolation

## Fleet install

The Sandbox page also generates fleet install scripts — clones and installs selected MCP repos from the fleet registry into a directory inside the sandbox.
