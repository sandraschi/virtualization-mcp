# Running Claude in Virtual Machines with vboxmcp

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Automated Claude Deployment](#automated-claude-deployment)
4. [Multi-VM Claude Networks](#multi-vm-claude-networks)
5. [Security Considerations](#security-considerations)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Introduction

This guide demonstrates how to use vboxmcp to create and manage virtual machines running Claude, including automated deployment, networking, and security best practices.

## Quick Start

### Prerequisites

- vboxmcp installed and configured
- VirtualBox 6.1 or later
- Sufficient system resources (CPU, RAM, disk space)
- Claude API access

### Basic Setup

1. **Create a base VM with Claude**

```python
from mcp.client import MCPClient

client = MCPClient("http://localhost:8000")

# Create a new VM
vm_name = "claude-dev"
client.create_vm(
    name=vm_name,
    template="ubuntu-20.04",
    memory_mb=8192,  # 8GB RAM recommended for Claude
    cpu_count=4,     # 4 vCPUs recommended
    disk_gb=50       # 50GB disk space
)

# Configure networking
client.configure_network(
    vm_name=vm_name,
    network_mode="nat",  # For internet access
    port_forwards=[
        {"name": "ssh", "host_port": 2222, "guest_port": 22},
        {"name": "api", "host_port": 8000, "guest_port": 8000}
    ]
)

# Start the VM
client.start_vm(vm_name)

# Install Claude (simplified example)
install_script = """
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip

# Install Claude Python client
pip3 install anthropic

# Create a simple Claude API server
cat > claude_server.py << 'EOL'
from fastapi import FastAPI, HTTPException
import anthropic

app = FastAPI()
client = anthropic.Client(api_key="YOUR_API_KEY")

@app.post("/chat")
asdef chat(prompt: str):
    try:
        response = client.completion(
            prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
            stop_sequences=["\n\nHuman:", "\n\n"],
            model="claude-v1",
            max_tokens_to_sample=1000,
        )
        return {"response": response["completion"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOL

# Run the server (in a real scenario, use a process manager)
nohup python3 claude_server.py > server.log 2>&1 &
"""

# Upload and run the installation script
client.upload_to_vm(vm_name, 
                   local_path=install_script, 
                   remote_path="/tmp/install_claude.sh")

client.execute_command(vm_name, "chmod +x /tmp/install_claude.sh && /tmp/install_claude.sh")
```

## Automated Claude Deployment

### Using DXT Packages

1. **Create a DXT package for Claude deployment**

```python
# dxt/claude_deploy.py
def deploy_claude(vm_name, api_key):
    """Deploy Claude to a VM."""
    # 1. Check if VM exists
    if not client.vm_exists(vm_name):
        raise ValueError(f"VM {vm_name} does not exist")
    
    # 2. Upload installation script
    script = f"""
    # Installation commands with API key
    pip3 install anthropic
    # ... rest of the installation ...
    """
    
    # 3. Execute installation
    client.upload_to_vm(vm_name, script, "/tmp/install.sh")
    client.execute_command(vm_name, "chmod +x /tmp/install.sh && /tmp/install.sh")
    
    return {"status": "success", "message": f"Claude deployed to {vm_name}"}
```

### Configuration Management

```python
# config/claude_config.json
{
    "vm_specs": {
        "memory_mb": 8192,
        "cpu_count": 4,
        "disk_gb": 50,
        "base_image": "ubuntu-20.04"
    },
    "network": {
        "mode": "nat",
        "port_forwards": [
            {"name": "ssh", "host_port": 2222, "guest_port": 22},
            {"name": "api", "host_port": 8000, "guest_port": 8000}
        ]
    },
    "claude": {
        "api_key_env_var": "CLAUDE_API_KEY",
        "model": "claude-v1",
        "max_tokens": 1000
    }
}
```

## Multi-VM Claude Networks

### Creating a Claude Cluster

```python
def create_claude_cluster(cluster_name, node_count=3):
    """Create a cluster of Claude VMs."""
    cluster = {}
    
    # Create each VM in the cluster
    for i in range(node_count):
        vm_name = f"{cluster_name}-node-{i+1}"
        
        # Create VM
        client.create_vm(
            name=vm_name,
            template="ubuntu-20.04",
            memory_mb=8192,
            cpu_count=4,
            disk_gb=50
        )
        
        # Configure internal network
        client.configure_network(
            vm_name=vm_name,
            network_mode="intnet",
            intnet_name=f"{cluster_name}-network"
        )
        
        # Deploy Claude
        deploy_claude(vm_name, os.getenv("CLAUDE_API_KEY"))
        
        cluster[vm_name] = {
            "status": "running",
            "internal_ip": f"10.0.0.{i+1}",
            "api_endpoint": f"http://10.0.0.{i+1}:8000/chat"
        }
    
    return cluster
```

### Load Balancing

```python
from fastapi import FastAPI, HTTPException
import random
import httpx

app = FastAPI()

# List of Claude API endpoints
CLAUDE_NODES = [
    "http://10.0.0.1:8000/chat",
    "http://10.0.0.2:8000/chat",
    "http://10.0.0.3:8000/chat"
]

@app.post("/chat")
async def chat(prompt: str):
    """Load balanced chat endpoint."""
    # Simple round-robin load balancing
    node = random.choice(CLAUDE_NODES)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                node,
                json={"prompt": prompt},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Security Considerations

### Important Warnings

1. **Rate Limiting**:
   - Implement rate limiting to prevent API abuse
   - Monitor usage to stay within API quotas

2. **API Key Protection**:
   - Never hardcode API keys in scripts
   - Use environment variables or secure secret management
   - Rotate API keys regularly

3. **Network Security**:
   - Use firewalls to restrict access to Claude VMs
   - Implement proper authentication and authorization
   - Use HTTPS for all API communications

### Secure Configuration

```python
# Example of secure Claude client setup
from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException, status

api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

@app.post("/secure-chat")
async def secure_chat(
    prompt: str,
    api_key: str = Depends(get_api_key)
):
    # Process the chat request
    pass
```

## Performance Optimization

### VM Configuration

- **CPU Pinning**: Pin vCPUs to physical cores
- **Memory Allocation**: Allocate sufficient memory (8GB+ recommended)
- **Disk I/O**: Use SSD storage for better performance
- **Network**: Use paravirtualized network adapters

### Claude-Specific Optimizations

```python
# Optimized Claude client configuration
client = anthropic.Client(
    api_key=os.getenv("CLAUDE_API_KEY"),
    max_retries=3,
    timeout=30.0,
    # Enable streaming for long responses
    stream=True
)

# Batch multiple requests when possible
async def batch_chat_requests(prompts):
    """Process multiple prompts in parallel."""
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(process_prompt(prompt))
            for prompt in prompts
        ]
    return [t.result() for t in tasks]
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify API key is valid
   - Check network connectivity
   - Ensure proper port forwarding

2. **Performance Issues**:
   - Monitor VM resource usage
   - Check for network latency
   - Verify Claude API status

3. **Authentication Failures**:
   - Verify API key permissions
   - Check for IP restrictions
   - Ensure proper authentication headers

### Logging and Monitoring

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"claude_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("claude-vm")

# Example usage
try:
    response = client.completion(prompt=prompt)
    logger.info(f"Successfully processed prompt: {prompt[:50]}...")
except Exception as e:
    logger.error(f"Error processing prompt: {str(e)}")
    raise
```

## Best Practices

### Development Workflow

1. **Use Version Control**:
   - Track all code and configuration changes
   - Use feature branches for new development
   - Implement code reviews

2. **Testing**:
   - Write unit tests for all functionality
   - Test in isolated environments
   - Implement CI/CD pipelines

3. **Documentation**:
   - Document all APIs and configurations
   - Keep documentation up to date
   - Include examples and tutorials

### Production Deployment

1. **High Availability**:
   - Deploy multiple Claude VMs
   - Implement load balancing
   - Set up monitoring and alerts

2. **Security**:
   - Use HTTPS with valid certificates
   - Implement proper authentication
   - Regularly update dependencies

3. **Scaling**:
   - Monitor performance metrics
   - Scale horizontally as needed
   - Implement auto-scaling when possible
