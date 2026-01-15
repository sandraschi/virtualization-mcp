use zed_extension_api as zed;

struct VirtualizationManagementExtension;

impl zed::Extension for VirtualizationManagementExtension {
    fn context_server_command(
        &mut self,
        id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> zed::Result<zed::Command> {
        match id.0.as_str() {
            "virtualization-mcp" => Ok(zed::Command {
                command: "uv".to_string(),
                args: vec!["run".to_string(), "virtualization_mcp.all_tools_server:main".to_string()],
                env: Default::default(),
            }),
            _ => Err(format!("Unknown server: {}", id.0)),
        }
    }
}

zed::register_extension!(VirtualizationManagementExtension);
