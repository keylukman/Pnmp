import { useMemo, useState } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Globe, Shield, Server, Radio, Wifi, Monitor, ArrowUpDown, Info } from 'lucide-react';

export default function TopologyPage() {
  const { devices, topologyLinks } = useDeviceStore();
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'visual' | 'list'>('visual');

  const topologyData = useMemo(() => {
    const internet = { id: 'internet', label: 'Internet', type: 'cloud', status: 'up' as const };
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

  const getDeviceIcon = (role: string, size: 'sm' | 'md' | 'lg' = 'md') => {
    const sizeClass = size === 'lg' ? 'w-6 h-6' : size === 'md' ? 'w-5 h-5' : 'w-4 h-4';
    switch (role) {
      case 'firewall': return <Shield className={sizeClass} />;
      case 'core_switch': return <Server className={sizeClass} />;
      case 'distribution_switch': return <Server className={sizeClass} />;
      case 'access_switch': return <Server className={sizeClass} />;
      case 'router': return <Globe className={sizeClass} />;
      case 'wireless_controller': return <Radio className={sizeClass} />;
      case 'access_point': return <Wifi className={sizeClass} />;
      case 'server': return <Monitor className={sizeClass} />;
      case 'load_balancer': return <ArrowUpDown className={sizeClass} />;
      default: return <Server className={sizeClass} />;
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

  const getDotColor = (status: string) => {
    switch (status) {
      case 'up': return 'bg-noc-success';
      case 'down': return 'bg-noc-danger';
      case 'warning': return 'bg-noc-warning';
      case 'maintenance': return 'bg-noc-info';
      default: return 'bg-noc-text-muted';
    }
  };

  const DeviceNode = ({ device, size = 'md' }: { device: typeof devices[0]; size?: 'sm' | 'md' | 'lg' }) => {
    const isSelected = selectedNode === device.id;
    return (
      <div
        onClick={() => setSelectedNode(isSelected ? null : device.id)}
        className={`topo-node cursor-pointer rounded-lg border p-3 text-center transition-all ${getStatusColor(device.status)} ${isSelected ? 'ring-2 ring-noc-primary ring-offset-1 ring-offset-noc-bg' : ''}`}
      >
        <div className={`flex items-center justify-center mb-1.5 ${getTextColor(device.status)}`}>
          {getDeviceIcon(device.deviceRole, size)}
        </div>
        <p className="text-[10px] font-medium text-noc-text truncate max-w-[100px]">{device.displayName}</p>
        <p className="text-[9px] text-noc-text-muted font-mono">{device.managementIp}</p>
        <div className={`w-1.5 h-1.5 rounded-full mx-auto mt-1 ${getDotColor(device.status)} ${device.status === 'up' ? 'animate-pulse' : ''}`} />
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Network Topology</h1>
          <p className="text-sm text-noc-text-muted">{devices.length} devices • {topologyLinks.length} links discovered</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-noc-surface border border-noc-border rounded-lg p-0.5">
            <button onClick={() => setViewMode('visual')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'visual' ? 'bg-noc-primary/10 text-noc-primary' : 'text-noc-text-muted hover:text-noc-text'}`}>
              Visual
            </button>
            <button onClick={() => setViewMode('list')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'list' ? 'bg-noc-primary/10 text-noc-primary' : 'text-noc-text-muted hover:text-noc-text'}`}>
              List
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 bg-noc-surface border border-noc-border rounded-lg px-4 py-2">
        <span className="text-xs text-noc-text-muted font-medium">Legend:</span>
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-noc-success" /><span className="text-xs text-noc-text-muted">UP</span></div>
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-noc-danger" /><span className="text-xs text-noc-text-muted">DOWN</span></div>
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-noc-warning" /><span className="text-xs text-noc-text-muted">WARNING</span></div>
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-noc-info" /><span className="text-xs text-noc-text-muted">MAINTENANCE</span></div>
        <span className="text-xs text-noc-text-muted ml-2">|</span>
        <div className="flex items-center gap-1.5"><span className="text-[10px] px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">LLDP</span><span className="text-xs text-noc-text-muted">Auto-discovered</span></div>
        <div className="flex items-center gap-1.5"><span className="text-[10px] px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">MANUAL</span><span className="text-xs text-noc-text-muted">Manual link</span></div>
      </div>

      {viewMode === 'visual' ? (
        <div className="bg-noc-surface border border-noc-border rounded-lg p-6 overflow-x-auto">
          <div className="min-w-[800px]">
            {/* Internet */}
            <div className="flex justify-center mb-6">
              <div className="px-6 py-3 rounded-xl border border-noc-border bg-noc-surface-2/50 text-center">
                <Globe className="w-6 h-6 text-noc-primary mx-auto mb-1" />
                <p className="text-xs font-medium text-noc-text">Internet</p>
                <p className="text-[10px] text-noc-text-muted">Multi-homed</p>
              </div>
            </div>

            {/* Connection lines from internet */}
            <div className="flex justify-center mb-2">
              <div className="w-px h-8 bg-noc-border" />
            </div>

            {/* ISP Routers / Load Balancer */}
            <div className="flex justify-center gap-4 mb-2">
              {topologyData.routers.filter(r => r.siteName === 'Internet Gateway').map(router => (
                <DeviceNode key={router.id} device={router} size="md" />
              ))}
            </div>

            {/* Lines down */}
            <div className="flex justify-center mb-2">
              <div className="w-px h-6 bg-noc-border" />
            </div>

            {/* Firewalls */}
            {topologyData.firewalls.length > 0 && (
              <>
                <div className="flex justify-center gap-4 mb-2">
                  {topologyData.firewalls.map(fw => (
                    <DeviceNode key={fw.id} device={fw} size="md" />
                  ))}
                </div>
                <div className="flex justify-center mb-2">
                  <div className="w-px h-6 bg-noc-border" />
                </div>
              </>
            )}

            {/* Core Switches */}
            {topologyData.coreSwitches.length > 0 && (
              <>
                <div className="flex justify-center gap-4 mb-2">
                  {topologyData.coreSwitches.map(cs => (
                    <DeviceNode key={cs.id} device={cs} size="lg" />
                  ))}
                </div>
                <div className="flex justify-center mb-2">
                  <div className="w-48 h-px bg-noc-border relative">
                    <div className="absolute left-1/4 top-0 w-px h-4 bg-noc-border" />
                    <div className="absolute left-1/2 top-0 w-px h-4 bg-noc-border" />
                    <div className="absolute left-3/4 top-0 w-px h-4 bg-noc-border" />
                  </div>
                </div>
              </>
            )}

            {/* Distribution + WLC + Servers */}
            <div className="flex justify-center gap-6 mb-2">
              <div className="flex gap-3">
                {topologyData.distSwitches.map(ds => (
                  <DeviceNode key={ds.id} device={ds} size="md" />
                ))}
              </div>
              <div className="flex gap-3">
                {topologyData.wlc.map(w => (
                  <DeviceNode key={w.id} device={w} size="md" />
                ))}
              </div>
              <div className="flex gap-3">
                {topologyData.servers.map(s => (
                  <DeviceNode key={s.id} device={s} size="md" />
                ))}
              </div>
            </div>

            {/* Lines down to access */}
            <div className="flex justify-center mb-2">
              <div className="w-64 h-px bg-noc-border relative">
                <div className="absolute left-0 top-0 w-px h-4 bg-noc-border" />
                <div className="absolute left-1/3 top-0 w-px h-4 bg-noc-border" />
                <div className="absolute left-2/3 top-0 w-px h-4 bg-noc-border" />
                <div className="absolute right-0 top-0 w-px h-4 bg-noc-border" />
              </div>
            </div>

            {/* Access switches + APs */}
            <div className="flex justify-center gap-4 flex-wrap">
              {topologyData.accessSwitches.map(as => (
                <DeviceNode key={as.id} device={as} size="sm" />
              ))}
              {topologyData.aps.map(ap => (
                <DeviceNode key={ap.id} device={ap} size="sm" />
              ))}
              {/* Devices not yet placed */}
              {devices.filter(d => !['firewall', 'core_switch', 'distribution_switch', 'router', 'wireless_controller', 'access_point', 'access_switch', 'server', 'load_balancer'].includes(d.deviceRole)).map(d => (
                <DeviceNode key={d.id} device={d} size="sm" />
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* List view */
        <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
          <table className="noc-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Role</th>
                <th>IP</th>
                <th>Status</th>
                <th>Connected To</th>
                <th>Link Type</th>
              </tr>
            </thead>
            <tbody>
              {devices.map(device => {
                const links = topologyLinks.filter(l => l.sourceDeviceId === device.id || l.targetDeviceId === device.id);
                const connectedNames = links.map(l => {
                  const otherId = l.sourceDeviceId === device.id ? l.targetDeviceId : l.sourceDeviceId;
                  const other = devices.find(d => d.id === otherId);
                  return other?.displayName || 'Unknown';
                });
                return (
                  <tr key={device.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className={getTextColor(device.status)}>{getDeviceIcon(device.deviceRole, 'sm')}</div>
                        <div>
                          <p className="text-xs font-medium text-noc-text">{device.displayName}</p>
                          <p className="text-[10px] text-noc-text-muted">{device.vendor} {device.model}</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-xs text-noc-text-muted">{device.deviceRole.replace(/_/g, ' ')}</td>
                    <td className="text-xs font-mono text-noc-text-muted">{device.managementIp}</td>
                    <td>
                      <span className={`inline-flex items-center gap-1 text-xs ${getTextColor(device.status)}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${getDotColor(device.status)}`} />
                        {device.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="text-xs text-noc-text-muted">{connectedNames.length > 0 ? connectedNames.join(', ') : '-'}</td>
                    <td className="text-xs">
                      {links.length > 0 ? (
                        <span className="px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted text-[10px]">
                          {links[0].linkType.toUpperCase()}
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Topology Links Table */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-noc-text mb-3 flex items-center gap-2">
          <Info className="w-4 h-4 text-noc-primary" />
          Discovered Links ({topologyLinks.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Source Port</th>
                <th></th>
                <th>Target Port</th>
                <th>Target</th>
                <th>Type</th>
                <th>Bandwidth</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {topologyLinks.map(link => {
                const source = devices.find(d => d.id === link.sourceDeviceId);
                const target = devices.find(d => d.id === link.targetDeviceId);
                return (
                  <tr key={link.id}>
                    <td className="text-xs text-noc-text">{source?.displayName || 'Unknown'}</td>
                    <td className="text-xs font-mono text-noc-text-muted">{link.sourceInterface}</td>
                    <td className="text-center text-noc-text-muted">
                      <span className={`inline-block w-8 h-px ${link.status === 'up' ? 'bg-noc-success' : 'bg-noc-danger'}`} />
                      ↔
                      <span className={`inline-block w-8 h-px ${link.status === 'up' ? 'bg-noc-success' : 'bg-noc-danger'}`} />
                    </td>
                    <td className="text-xs font-mono text-noc-text-muted">{link.targetInterface}</td>
                    <td className="text-xs text-noc-text">{target?.displayName || 'Unknown'}</td>
                    <td>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">
                        {link.linkType.toUpperCase()}
                      </span>
                    </td>
                    <td className="text-xs text-noc-text-muted">{link.bandwidth}</td>
                    <td>
                      <span className={`inline-flex items-center gap-1 text-xs ${link.status === 'up' ? 'text-noc-success' : 'text-noc-danger'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${link.status === 'up' ? 'bg-noc-success' : 'bg-noc-danger'}`} />
                        {link.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected device detail */}
      {selectedNode && (
        <div className="bg-noc-surface border border-noc-primary/30 rounded-lg p-4">
          {(() => {
            const device = devices.find(d => d.id === selectedNode);
            if (!device) return null;
            const links = topologyLinks.filter(l => l.sourceDeviceId === device.id || l.targetDeviceId === device.id);
            return (
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getStatusColor(device.status)}`}>
                  <div className={getTextColor(device.status)}>{getDeviceIcon(device.deviceRole, 'lg')}</div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-noc-text">{device.displayName}</h4>
                    <span className={`text-xs ${getTextColor(device.status)}`}>{device.status.toUpperCase()}</span>
                  </div>
                  <p className="text-xs text-noc-text-muted mt-0.5">{device.vendor} {device.model} • {device.managementIp} • {device.siteName}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-noc-text-muted">
                    <span>CPU: {device.cpu}%</span>
                    <span>Memory: {device.memory}%</span>
                    <span>Uptime: {device.uptime}</span>
                    <span>Links: {links.length}</span>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
