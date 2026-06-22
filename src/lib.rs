use zed_extension_api as zed;

struct VirtualizationManagementExtension;

impl zed::Extension for VirtualizationManagementExtension {
    fn new() -> Self {
        Self
    }

    fn context_server_command(
        &mut self,
        _id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> zed::Result<zed::Command> {
        Ok(zed::Command {
            command: "uv".to_string(),
            args: vec![
                "run".to_string(),
                "virtualization_mcp.all_tools_server:main".to_string(),
            ],
            env: Default::default(),
        })
    }
}

zed::register_extension!(VirtualizationManagementExtension);
