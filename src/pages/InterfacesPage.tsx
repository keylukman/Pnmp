import { useState, useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Search, Filter, ArrowUpRight, ArrowDownRight, AlertCircle } from 'lucide-react';

export default function InterfacesPage() {
  const { interfaces, devices } = useDeviceStore();
  const [search, setSearch] = useState('');
  const [deviceFilter, setDeviceFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredInterfaces = useMemo(() => {
    return interfaces.filter((i) => {
      const matchSearch = !search || i.name.toLowerCase().includes(search.toLowerCase()) || i.description.toLowerCase().includes(search.toLowerCase()) || i.deviceName.toLowerCase().includes(search.toLowerCase());
      const matchDevice = deviceFilter === 'all' || i.deviceId === deviceFilter;
      const matchStatus = statusFilter === 'all' || i.status === statusFilter;
      return matchSearch && matchDevice && matchStatus;
    });
  }, [interfaces, search, deviceFilter, statusFilter]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1000;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getUtilColor = (util: number) => {
    if (util > 80) return 'text-noc-danger';
    if (util > 60) return 'text-noc-warning';
    return 'text-noc-success';
  };

  const getBarColor = (util: number) => {
    if (util > 80) return 'bg-noc-danger';
    if (util > 60) return 'bg-noc-warning';
    return 'bg-noc-success';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Interfaces</h1>
          <p className="text-sm text-noc-text-muted">{filteredInterfaces.length} interfaces monitored</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-noc-surface border border-noc-border rounded-lg p-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-noc-text-muted" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search interfaces..." className="w-full pl-9 pr-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary" />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-noc-text-muted" />
          <select value={deviceFilter} onChange={(e) => setDeviceFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="all">All Devices</option>
            {devices.map((d) => <option key={d.id} value={d.id}>{d.displayName}</option>)}
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="all">All Status</option>
            <option value="up">UP</option>
            <option value="down">DOWN</option>
          </select>
        </div>
      </div>

      {/* Interface table */}
      <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>Interface</th>
                <th>Device</th>
                <th>Description</th>
                <th>Status</th>
                <th>Speed</th>
                <th>RX</th>
                <th>TX</th>
                <th>Utilization</th>
                <th>Errors</th>
                <th>Discards</th>
              </tr>
            </thead>
            <tbody>
              {filteredInterfaces.map((iface) => (
                <tr key={iface.id}>
                  <td className="font-mono text-xs font-medium">{iface.name}</td>
                  <td className="text-xs">{iface.deviceName}</td>
                  <td className="text-xs text-noc-text-muted max-w-[150px] truncate">{iface.description}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${iface.status === 'up' ? 'text-noc-success' : 'text-noc-danger'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${iface.status === 'up' ? 'bg-noc-success' : 'bg-noc-danger'}`} />
                      {iface.status === 'up' ? 'UP' : iface.status === 'down' ? 'DOWN' : 'ADMIN DOWN'}
                    </span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{iface.speed}</td>
                  <td>
                    <div className="flex items-center gap-1">
                      <ArrowDownRight className="w-3 h-3 text-noc-primary" />
                      <span className="text-xs text-noc-text-muted">{formatBytes(iface.rxBytes)}/s</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <ArrowUpRight className="w-3 h-3 text-noc-success" />
                      <span className="text-xs text-noc-text-muted">{formatBytes(iface.txBytes)}/s</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-noc-bg rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${getBarColor(iface.utilization)}`} style={{ width: `${iface.utilization}%` }} />
                      </div>
                      <span className={`text-xs font-medium ${getUtilColor(iface.utilization)}`}>{iface.utilization}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`text-xs ${iface.rxErrors + iface.txErrors > 0 ? 'text-noc-warning flex items-center gap-1' : 'text-noc-text-muted'}`}>
                      {iface.rxErrors + iface.txErrors > 0 && <AlertCircle className="w-3 h-3" />}
                      {iface.rxErrors + iface.txErrors}
                    </span>
                  </td>
                  <td>
                    <span className={`text-xs ${iface.rxDiscards + iface.txDiscards > 0 ? 'text-noc-warning' : 'text-noc-text-muted'}`}>
                      {iface.rxDiscards + iface.txDiscards}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredInterfaces.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-sm text-noc-text-muted">No interfaces found matching your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
