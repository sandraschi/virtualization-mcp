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
1. Pick **Dev Infra** (basic tooling) or **Full Dev** (all tools)
2. Check the tools you want (Python, Git, Node, VS Code, etc.)
3. Click **Launch Windows Sandbox**

It generates a `.wsb` file and opens it — sandbox boots with your tools installing automatically.

## Dev setup options

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
