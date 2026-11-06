import { AlertTriangle, Cpu, HardDrive, Monitor } from "lucide-react";

export default function Hackintosh() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-2xl font-bold">Hackintosh Lab</h2>
        <p className="text-sm text-muted-foreground">
          macOS on non-Apple hardware. Intel notebooks first, Goliath VM only for slow tests.
        </p>
      </div>

      <div className="p-4 rounded-xl border border-yellow-500/20 bg-yellow-500/10 text-sm flex gap-3">
        <AlertTriangle className="w-5 h-5 shrink-0" />
        <div>
          Apple EULA allows virtualised macOS only on Apple hardware. Bare-metal and vmrun guides here are
          for personal experimentation. Community Unlocker is unofficial and unsupported by this project -
          the MCP only drives vmrun, it never downloads Unlocker or macOS images.
        </div>
      </div>

      <section className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
        <h3 className="font-bold flex items-center gap-2"><Cpu className="w-4 h-4" /> What to use</h3>
        <ul className="text-sm space-y-1 list-disc pl-5 text-muted-foreground">
          <li><b>Best:</b> Intel 8th-10th gen notebook (ThinkPad T490/X1C7, Dell 7390/7400). Native UHD 620/630 Metal, sleep works, Dortania OpenCore guide mature.</li>
          <li><b>RAM floor:</b> 16GB for Xcode 26 (macOS 6GB + Xcode/Sim 6-8GB + AI agent). 24-32GB sweet spot. T490 goes to 40GB (8 soldered + 32 slot).</li>
          <li><b>Avoid:</b> AMD mobile (broken sleep/iGPU, patch every update), Snapdragon ARM (cannot run x86 macOS 26), 8GB soldered-only.</li>
          <li><b>Target:</b> macOS 26 Tahoe - last Intel release, required for Xcode 26. macOS 27 is ARM-only.</li>
        </ul>
      </section>

      <section className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
        <h3 className="font-bold flex items-center gap-2"><Monitor className="w-4 h-4" /> Goliath slow-test path</h3>
        <ol className="text-sm space-y-1 list-decimal pl-5 text-muted-foreground">
          <li>Install VMware Workstation Pro (free) - see VMware page status card. No-login mirror in docs/hackintosh.md.</li>
          <li>Get Tahoe (25G76) via gibMacOS publicrelease catalog - direct from Apple, docs/hackintosh.md has the commands.</li>
          <li>Create macOS 26 VM: 8 vCPU, 16GB RAM, 80GB NVMe, darwin guestOS, smc.version=0 (Unlocker).</li>
          <li>Snapshot clean install first - VMware page Take button.</li>
          <li>Expect: CLI xcodebuild OK, Simulator crawls (no Nvidia Metal driver on 4090).</li>
          <li>Use Intel notebook for daily Xcode, Goliath VM for headless build checks.</li>
        </ol>
      </section>

      <section className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
        <h3 className="font-bold flex items-center gap-2"><HardDrive className="w-4 h-4" /> Why AI revived this</h3>
        <p className="text-sm text-muted-foreground">
          Classic work was DSDT/ACPI patches, kext shims, framebuffer drivers - months of expert labour.
          Agents + Ghidra now draft OpenCore patches and iterate on kernel panics overnight, which is why
          Snapdragon/RK3588/Switch ports appeared in weeks. Still lab toys without GPU accel.
        </p>
      </section>
    </div>
  );
}
