import {
  Camera,
  Loader2,
  Monitor,
  Pause,
  Play,
  Plus,
  Power,
  RefreshCw,
  RotateCcw,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface VmwareVm {
  name: string;
  vmx_path: string;
  state: string;
  guest_os: string;
  memory_mb: number;
  cpus: number;
  provider?: string;
}

export default function Vmware() {
  const [vms, setVms] = useState<VmwareVm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionVm, setActionVm] = useState<string | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [snapName, setSnapName] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [snapshots, setSnapshots] = useState<
    Record<string, { name: string }[]>
  >({});
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    memory_mb: 4096,
    cpus: 2,
    disk_gb: 40,
    guest_os: "ubuntu-64",
    firmware: "efi",
    iso_path: "",
  });

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/status`);
      if (res.ok) {
        const data = await res.json();
        setAvailable(data.available ?? null);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const fetchVMs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/vms`);
      if (res.ok) {
        const data = await res.json();
        setVms(data.vms || []);
        setError(null);
      } else {
        const data = await res.json().catch(() => ({}));
        setError(
          data.detail ||
            "VMware vmrun not found. Install Workstation Pro (free).",
        );
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchVMs();
  }, [fetchStatus, fetchVMs]);

  const doAction = async (
    vmx_path: string,
    action: string,
    extra: any = {},
  ) => {
    setActionVm(`${vmx_path}-${action}`);
    try {
      await fetch(`${API_BASE}/api/v1/vmware/action?action=${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vmx_path, ...extra }),
      });
      setTimeout(fetchVMs, 1000);
    } catch {
      /* ignore */
    }
    setActionVm(null);
  };

  const doCreate = async () => {
    if (!form.name.trim()) {
      setCreateError("Name is required.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          memory_mb: Number(form.memory_mb),
          cpus: Number(form.cpus),
          disk_gb: Number(form.disk_gb),
          guest_os: form.guest_os || undefined,
          firmware: form.firmware,
          iso_path: form.iso_path.trim() || undefined,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Create failed");
      setForm({
        name: "",
        memory_mb: 4096,
        cpus: 2,
        disk_gb: 40,
        guest_os: "ubuntu-64",
        firmware: "efi",
        iso_path: "",
      });
      setShowCreate(false);
      setTimeout(fetchVMs, 1000);
    } catch (e: any) {
      setCreateError(e.message);
    } finally {
      setCreating(false);
    }
  };

  const doDelete = async (vmx_path: string) => {
    if (
      !window.confirm(
        `Delete this VMware VM?\n${vmx_path}\n\nStops it and removes its folder.`,
      )
    )
      return;
    setActionVm(`${vmx_path}-delete`);
    try {
      await fetch(`${API_BASE}/api/v1/vmware/action?action=delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vmx_path }),
      });
      setTimeout(fetchVMs, 1000);
    } catch {
      /* ignore */
    }
    setActionVm(null);
  };

  const loadSnapshots = async (vmx_path: string) => {
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/vmware/action?action=snapshot_list`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ vmx_path }),
        },
      );
      if (res.ok) {
        const data = await res.json();
        setSnapshots((prev) => ({ ...prev, [vmx_path]: data.snapshots || [] }));
      }
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">VMware Workstation Pro</h2>
          <p className="text-sm text-muted-foreground">
            Free since Broadcom Nov 2024. Best Windows option for macOS guests
            (Unlocker, EULA-grey).
            {available === false && " vmrun not detected."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm"
          >
            <Plus className="w-4 h-4" /> New VM
          </button>
          <button
            type="button"
            onClick={() => {
              fetchStatus();
              fetchVMs();
            }}
            className="p-2 hover:bg-white/5 rounded-lg"
            aria-label="Refresh VMware VMs"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="p-4 rounded-xl border border-border bg-card/40 space-y-3">
          <div className="font-semibold text-sm">
            Create VMware VM{" "}
            <span className="text-muted-foreground font-normal">
              (.vmx + .vmdk under Documents/Virtual Machines)
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Name (e.g. ubuntu-dev)"
              className="col-span-2 px-3 py-1.5 rounded-lg bg-background border border-border text-sm"
            />
            <select
              value={form.guest_os}
              onChange={(e) => setForm({ ...form, guest_os: e.target.value })}
              className="px-3 py-1.5 rounded-lg bg-background border border-border text-sm"
            >
              <option value="ubuntu-64">Ubuntu 64-bit</option>
              <option value="debian12-64">Debian 12 64-bit</option>
              <option value="fedora-64">Fedora 64-bit</option>
              <option value="windows11-64">Windows 11 64-bit</option>
              <option value="windows10-64">Windows 10 64-bit</option>
              <option value="darwin23-64">macOS (Unlocker, EULA-grey)</option>
            </select>
            <select
              value={form.firmware}
              onChange={(e) => setForm({ ...form, firmware: e.target.value })}
              className="px-3 py-1.5 rounded-lg bg-background border border-border text-sm"
            >
              <option value="efi">UEFI</option>
              <option value="bios">BIOS</option>
            </select>
            <label className="text-xs text-muted-foreground">
              RAM (MB)
              <input
                type="number"
                value={form.memory_mb}
                min={512}
                step={512}
                onChange={(e) =>
                  setForm({ ...form, memory_mb: Number(e.target.value) })
                }
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-sm text-foreground"
              />
            </label>
            <label className="text-xs text-muted-foreground">
              vCPUs
              <input
                type="number"
                value={form.cpus}
                min={1}
                max={32}
                onChange={(e) =>
                  setForm({ ...form, cpus: Number(e.target.value) })
                }
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-sm text-foreground"
              />
            </label>
            <label className="text-xs text-muted-foreground">
              Disk (GB)
              <input
                type="number"
                value={form.disk_gb}
                min={4}
                onChange={(e) =>
                  setForm({ ...form, disk_gb: Number(e.target.value) })
                }
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-sm text-foreground"
              />
            </label>
            <label className="text-xs text-muted-foreground">
              Installer ISO (optional)
              <input
                value={form.iso_path}
                onChange={(e) => setForm({ ...form, iso_path: e.target.value })}
                placeholder="C:\ISOs\ubuntu.iso"
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-sm text-foreground"
              />
            </label>
          </div>
          {createError && (
            <div className="text-xs text-red-400">{createError}</div>
          )}
          <button
            type="button"
            onClick={doCreate}
            disabled={creating}
            className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create VM"}
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl border border-yellow-500/20 bg-yellow-500/10 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading VMware VMs...
        </div>
      ) : vms.length === 0 ? (
        <div className="p-8 text-center rounded-xl border border-border bg-card/40 text-muted-foreground text-sm">
          No VMware VMs found. Use New VM above to create one under
          Documents/Virtual Machines.
        </div>
      ) : (
        <div className="grid gap-3">
          {vms.map((vm) => (
            <div
              key={vm.vmx_path}
              className="p-4 rounded-xl border border-border bg-card/40"
            >
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <Monitor className="w-5 h-5 text-primary" />
                  <div>
                    <div className="font-semibold">{vm.name}</div>
                    <div className="text-xs text-muted-foreground font-mono truncate max-w-[420px]">
                      {vm.vmx_path}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {vm.state} - {vm.guest_os} - {vm.memory_mb} MB - {vm.cpus}{" "}
                      vCPU
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                  <button
                    type="button"
                    onClick={() => doAction(vm.vmx_path, "start")}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Start (nogui)"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => doAction(vm.vmx_path, "stop")}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Stop (soft)"
                  >
                    <Power className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => doAction(vm.vmx_path, "suspend")}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Suspend"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => doAction(vm.vmx_path, "reset")}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Reset"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (expanded === vm.vmx_path) setExpanded(null);
                      else {
                        setExpanded(vm.vmx_path);
                        loadSnapshots(vm.vmx_path);
                      }
                    }}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Snapshots"
                  >
                    <Camera className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => doDelete(vm.vmx_path)}
                    className="p-2 hover:bg-white/5 rounded-lg text-red-400"
                    title="Delete VM"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  {actionVm?.startsWith(vm.vmx_path) && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                </div>
              </div>
              {expanded === vm.vmx_path && (
                <div className="mt-3 pt-3 border-t border-border/50 space-y-2">
                  <div className="flex gap-2">
                    <input
                      value={snapName}
                      onChange={(e) => setSnapName(e.target.value)}
                      placeholder="Snapshot name"
                      className="flex-1 px-3 py-1.5 rounded-lg bg-background border border-border text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        doAction(vm.vmx_path, "snapshot_create", {
                          snapshot_name: snapName,
                        });
                        setSnapName("");
                        setTimeout(() => loadSnapshots(vm.vmx_path), 1500);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm"
                    >
                      Take
                    </button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {(snapshots[vm.vmx_path] || []).length === 0
                      ? "No snapshots."
                      : (snapshots[vm.vmx_path] || [])
                          .map((s) => s.name)
                          .join(", ")}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
