// API utilities for calling MCP server tools
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10761';

export interface MCPToolCallRequest {
  tool: string;
  action: string;
  params?: Record<string, any>;
}

export interface MCPToolCallResponse {
  success: boolean;
  action: string;
  data?: any;
  error?: string;
  count?: number;
}

export async function callMCPTool(request: MCPToolCallRequest): Promise<MCPToolCallResponse> {
  const response = await fetch(`${API_BASE}/api/mcp/tool`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`MCP tool call failed: ${error}`);
  }
  
  return response.json();
}

// VM Management helpers
export async function listVMs(): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'list' });
}

export async function getVMInfo(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'info', params: { vm_name: vmName } });
}

export async function startVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'start', params: { vm_name: vmName } });
}

export async function stopVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'stop', params: { vm_name: vmName } });
}

export async function pauseVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'pause', params: { vm_name: vmName } });
}

export async function resumeVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'resume', params: { vm_name: vmName } });
}

export async function resetVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'reset', params: { vm_name: vmName } });
}

export async function deleteVM(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'delete', params: { vm_name: vmName } });
}

export async function createVM(params: {
  vm_name: string;
  os_type: string;
  memory_mb: number;
  disk_size_gb: number;
}): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'vm_management', action: 'create', params });
}

export async function cloneVM(sourceVm: string, newVmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'vm_management',
    action: 'clone',
    params: { source_vm: sourceVm, new_vm_name: newVmName },
  });
}

// Snapshot Management helpers
export async function listSnapshots(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'snapshot_management',
    action: 'list',
    params: { vm_name: vmName },
  });
}

export async function createSnapshot(
  vmName: string,
  snapshotName: string,
  description?: string
): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'snapshot_management',
    action: 'create',
    params: { vm_name: vmName, snapshot_name: snapshotName, description },
  });
}

export async function restoreSnapshot(vmName: string, snapshotName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'snapshot_management',
    action: 'restore',
    params: { vm_name: vmName, snapshot_name: snapshotName },
  });
}

export async function deleteSnapshot(vmName: string, snapshotName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'snapshot_management',
    action: 'delete',
    params: { vm_name: vmName, snapshot_name: snapshotName },
  });
}

// Network Management helpers
export async function listNetworks(): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'network_management', action: 'list_networks' });
}

export async function createNetwork(params: {
  network_name: string;
  ip_address?: string;
  netmask?: string;
}): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'network_management',
    action: 'create_network',
    params,
  });
}

export async function removeNetwork(networkName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'network_management',
    action: 'remove_network',
    params: { network_name: networkName },
  });
}

export async function listNetworkAdapters(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'network_management',
    action: 'list_adapters',
    params: { vm_name: vmName },
  });
}

// Storage Management helpers
export async function listStorageControllers(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'storage_management',
    action: 'list_controllers',
    params: { vm_name: vmName },
  });
}

export async function createStorageController(params: {
  vm_name: string;
  controller_name: string;
  controller_type: string;
}): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'storage_management',
    action: 'create_controller',
    params,
  });
}

export async function removeStorageController(params: {
  vm_name: string;
  controller_name: string;
}): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'storage_management',
    action: 'remove_controller',
    params,
  });
}

export async function listDisks(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'storage_management',
    action: 'list_disks',
    params: { vm_name: vmName },
  });
}

// System Management helpers
export async function getHostInfo(): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'system_management', action: 'host_info' });
}

export async function getVBoxVersion(): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'system_management', action: 'vbox_version' });
}

export async function listOSTypes(): Promise<MCPToolCallResponse> {
  return callMCPTool({ tool: 'system_management', action: 'ostypes' });
}

export async function getVMMetrics(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'system_management',
    action: 'metrics',
    params: { vm_name: vmName },
  });
}

export async function takeVMScreenshot(vmName: string): Promise<MCPToolCallResponse> {
  return callMCPTool({
    tool: 'system_management',
    action: 'screenshot',
    params: { vm_name: vmName },
  });
}
