# Claude Desktop Configuration for virtualization-mcp

## Prerequisites

1. **Install UV**: Make sure you have `uv` installed and in your PATH
   ```powershell
   # Check if uv is installed
   uv --version
   ```

2. **Install the package**: Run from the project directory
   ```powershell
   cd d:\Dev\repos\virtualization-mcp
   uv sync --dev
   ```

3. **Verify installation**: Test that the module can be imported
   ```powershell
   uv run python -c "import virtualization_mcp; print(virtualization_mcp.__version__)"
   ```

## Claude Desktop Configuration

### Location of Configuration File

The Claude Desktop configuration file is located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Which typically expands to:
```
C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json
```

### Configuration Content

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "d:\\Dev\\repos\\virtualization-mcp",
        "python",
        "-m",
        "virtualization_mcp"
      ],
      "env": {
        "VBOX_INSTALL_PATH": "C:\\Program Files\\Oracle\\VirtualBox",
        "VBOX_USER_HOME": "%USERPROFILE%\\VirtualBox VMs",
        "DEBUG": "true",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Important Notes

1. **Use `uv` command**: The configuration uses `uv run` instead of plain `python` to ensure the package is available in the correct environment.

2. **Directory Path**: Make sure the `--directory` argument points to your actual project location. Update `d:\\Dev\\repos\\virtualization-mcp` if your project is in a different location.

3. **VirtualBox Path**: Update `VBOX_INSTALL_PATH` if your VirtualBox is installed in a different location.

4. **User Home**: The `VBOX_USER_HOME` uses `%USERPROFILE%` which will be expanded by Windows. You can also use an absolute path if needed.

5. **Debug Mode**: Set `DEBUG` to `"false"` in production for less verbose logging.

## Applying the Configuration

1. **Create/Edit the config file**:
   ```powershell
   # Open in notepad
   notepad "%APPDATA%\Claude\claude_desktop_config.json"
   ```

2. **Paste the configuration** from above (adjust paths as needed)

3. **Restart Claude Desktop** completely:
   - Close all Claude Desktop windows
   - Quit from system tray if running
   - Start Claude Desktop again

4. **Verify in Claude**:
   - Open Claude Desktop
   - Look for the hammer icon (🔨) in the bottom right
   - Click it and you should see "virtualization-mcp" listed
   - The server status should show as connected

## Troubleshooting

### Server doesn't appear in Claude

1. Check that the config file is in the correct location
2. Verify JSON syntax is valid (no trailing commas, proper brackets)
3. Check Claude Desktop logs at:
   ```
   %APPDATA%\Claude\logs
   ```

### Server shows as disconnected

1. Test the command manually:
   ```powershell
   cd d:\Dev\repos\virtualization-mcp
   uv run python -m virtualization_mcp
   ```
   
2. If it fails, check:
   - Is `uv` in your PATH?
   - Is the project directory correct?
   - Are there any Python errors?

### Module not found error

This usually means the package isn't installed. Run:
```powershell
cd d:\Dev\repos\virtualization-mcp
uv sync --dev
```

### VirtualBox not found

1. Verify VirtualBox is installed
2. Check the installation path in the config matches your actual installation
3. Try the default path: `C:\Program Files\Oracle\VirtualBox`

## Alternative: Using Installed Package

If you install the package globally (not recommended for development):

```powershell
# Install globally
pip install -e d:\Dev\repos\virtualization-mcp

# Then you can use this simpler config:
{
  "mcpServers": {
    "virtualization-mcp": {
      "command": "python",
      "args": ["-m", "virtualization_mcp"],
      "env": {
        "VBOX_INSTALL_PATH": "C:\\Program Files\\Oracle\\VirtualBox",
        "DEBUG": "true"
      }
    }
  }
}
```

However, for development, using `uv run` is preferred as it isolates the environment.

## Testing the Connection

Once configured and Claude Desktop is restarted:

1. Open a new chat in Claude
2. Try a simple command:
   ```
   List all virtual machines
   ```
3. Claude should use the virtualization-mcp tools to respond

If you see tool calls happening, congratulations! Your server is working! 🎉



