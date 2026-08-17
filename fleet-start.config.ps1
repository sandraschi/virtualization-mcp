# Per-repo fleet start config for virtualization-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'virtualization-mcp'
    BackendPort  = 10701
    FrontendPort = 10700
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\virtualization-mcp\webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'virtualization_mcp.web.app:app'
        Env           = @{ WEB_PORT = '10701' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
