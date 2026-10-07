import { useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Globe, Shield, Server, Radio, Wifi, Monitor } from 'lucide-react';

export default function TopologyPage() {
  const { devices } = useDeviceStore();

  const topologyData = useMemo(() => {
    const internet = { id: 'internet', label: 'Internet', type: 'cloud', status: 'up' };
    const firewalls = devices.filter(d => d.deviceRole === 'firewall');
    const coreSwitches = devices.filter(d => d.deviceRole === 'core_switch');
    const distSwitches = devices.filter(d => d.deviceRole === 'distribution_switch');
    const routers = devices.filter(d => d.deviceRole === 'router');
    const wlc = devices.filter(d => d.deviceRole === 'wireless_controller');
    const aps = devices.filter(d => d.deviceRole === 'access_point');
    const accessSwitches = devices.filter(d => d.deviceRole === 'access_switch');
    const servers = devices.filter(d => d.deviceRole === 'server' || d.deviceRole === 'load_balancer');

    return { internet, firewalls, coreSwitches, distSwitches, routers, wlc, aps, accessSwitches, servers };
  }, [devices]);

  const getDeviceIcon = (role: string) => {
    switch (role) {
      case 'firewall': return <Shield className="w-5 h-5" />;
      case 'core_switch': return <Server className="w-5 h-5" />;
      case 'distribution_switch': return <Server className="w-4 h-4" />;
      case 'access_switch': return <Server className="w-4 h-4" />;
      case 'router': return <Globe className="w-5 h-5" />;
      case 'wireless_controller': return <Radio className="w-5 h-5" />;
      case 'access_point': return <Wifi className="w-4 h-4" />;
      case 'server': return <Monitor className="w-4 h-4" />;
      default: return <Server className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up': return 'border-noc-success bg-noc-success/5';
      case 'down': return 'border-noc-danger bg-noc-danger/5';
      case 'warning': return 'border-noc-warning bg-noc-warning/5';
      case 'maintenance': return 'border-noc-info bg-noc-info/5';
      default: return 'border-noc-border bg-noc-surface';
    }
  };

  const getTextColor = (status: string) => {
    switch (status) {
      case 'up': return 'text-noc-success';
      case 'down': return 'text-noc-danger';
      case 'warning': return 'text-noc-warning';
      case 'maintenance': return 'text-noc-info';
      default: return 'text-noc-text-muted';
    }
  };

  const NodeCard = ({ device }: { device: typeof devices[0] }) => (
    <div className={`topology-node border rounded-lg p-2.5 min-w-[120px] text-center cursor-pointer ${getStatusColor(device.status)}`}>
      <div className={`mx-auto mb-1 ${getTextColor(device.status)}`}>
        {getDeviceIcon(device.deviceRole)}
      </div>
      <p className="text-[10px] font-medium text-noc-text truncate">{device.displayName}</p>
      <p className="text-[9px] text-noc-text-muted font-mono">{device.managementIp}</p>
      <div className={`w-1.5 h-1.5 rounded-full mx-auto mt-1 ${device.status === 'up' ? 'bg-noc-success' : device.status === 'down' ? 'bg-noc-danger' : device.status === 'warning' ? 'bg-noc-warning' : 'bg-noc-info'}`} />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Network Topology</h1>
          <p className="text-sm text-noc-text-muted">Visual representation of network infrastructure</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-noc-text-muted">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-success"></span> UP</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-danger"></span> DOWN</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-warning"></span> WARNING</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-info"></span> MAINT</span>
        </div>
      </div>

      {/* Topology visualization */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-6 overflow-x-auto">
        <div className="min-w-[800px] flex flex-col items-center gap-4">
          {/* Internet */}
          <div className="border border-noc-primary/30 bg-noc-primary/5 rounded-xl px-8 py-3 text-center">
            <Globe className="w-6 h-6 text-noc-primary mx-auto mb-1" />
            <p className="text-sm font-medium text-noc-primary">Internet</p>
          </div>

          {/* Connection line */}
          <div className="w-px h-6 bg-noc-border" />

          {/* Firewalls */}
          <div className="flex items-center gap-6">
            {topologyData.firewalls.map((fw) => (
              <NodeCard key={fw.id} device={fw} />
            ))}
          </div>

          {/* Connection lines */}
          <div className="flex items-center gap-6">
            {topologyData.firewalls.map((fw) => (
              <div key={`line-${fw.id}`} className="w-px h-6 bg-noc-border" />
            ))}
          </div>

          {/* Routers */}
          <div className="flex items-center gap-4">
            {topologyData.routers.map((r) => (
              <NodeCard key={r.id} device={r} />
            ))}
          </div>

          {/* Connection line */}
          <div className="w-px h-6 bg-noc-border" />

          {/* Core Switch */}
          <div className="flex items-center gap-6">
            {topologyData.coreSwitches.map((cs) => (
              <NodeCard key={cs.id} device={cs} />
            ))}
          </div>

          {/* Connection lines to distribution */}
          <div className="w-px h-6 bg-noc-border" />

          {/* Distribution Switches */}
          <div className="flex items-center gap-4">
            {topologyData.distSwitches.map((ds) => (
              <NodeCard key={ds.id} device={ds} />
            ))}
          </div>

          {/* Connection lines */}
          <div className="flex items-center gap-4">
            {topologyData.distSwitches.length > 0 && (
              <>
                <div className="w-px h-6 bg-noc-border" />
                <div className="w-px h-6 bg-noc-border" />
              </>
            )}
          </div>

          {/* Access layer */}
          <div className="flex items-start gap-8">
            {/* Access Switches */}
            <div className="flex flex-col items-center gap-2">
              <p className="text-[10px] text-noc-text-muted uppercase tracking-wider mb-1">Access Switches</p>
              <div className="flex items-center gap-3">
                {topologyData.accessSwitches.map((as) => (
                  <NodeCard key={as.id} device={as} />
                ))}
              </div>
            </div>

            {/* Wireless */}
            <div className="flex flex-col items-center gap-2">
              <p className="text-[10px] text-noc-text-muted uppercase tracking-wider mb-1">Wireless</p>
              <div className="flex items-center gap-3">
                {topologyData.wlc.map((w) => (
                  <NodeCard key={w.id} device={w} />
                ))}
              </div>
              <div className="flex items-center gap-3 mt-2">
                {topologyData.aps.map((ap) => (
                  <NodeCard key={ap.id} device={ap} />
                ))}
              </div>
            </div>

            {/* Servers */}
            <div className="flex flex-col items-center gap-2">
              <p className="text-[10px] text-noc-text-muted uppercase tracking-wider mb-1">Servers / Security</p>
              <div className="flex items-center gap-3">
                {topologyData.servers.map((s) => (
                  <NodeCard key={s.id} device={s} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Topology info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">LLDP Neighbors</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Aruba CX Core → CCR-01</span>
              <span className="text-noc-success">Active</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Aruba CX Core → CCR-02</span>
              <span className="text-noc-success">Active</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Cisco 3750 → Aruba CX Core</span>
              <span className="text-noc-success">Active</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">FortiGate 200G → CCR-01</span>
              <span className="text-noc-success">Active</span>
            </div>
          </div>
        </div>

        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Network Segments</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Core Network</span>
              <span className="text-noc-text">10.1.0.0/16</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">WAN / Gateway</span>
              <span className="text-noc-text">10.2.0.0/24</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Data Center</span>
              <span className="text-noc-text">10.0.0.0/24</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Management</span>
              <span className="text-noc-text">10.255.0.0/24</span>
            </div>
          </div>
        </div>

        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Topology Stats</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Total Nodes</span>
              <span className="text-noc-text font-medium">{devices.length}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Active Links</span>
              <span className="text-noc-text font-medium">4</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Network Layers</span>
              <span className="text-noc-text font-medium">3 (Core/Dist/Access)</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-noc-text-muted">Discovery Protocol</span>
              <span className="text-noc-text font-medium">LLDP</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
