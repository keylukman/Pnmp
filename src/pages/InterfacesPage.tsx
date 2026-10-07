import { useState, useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Search, Filter, ArrowUpRight, ArrowDownRight, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export default function InterfacesPage() {
  const { interfaces, devices } = useDeviceStore();
  const [search, setSearch] = useState('');
  const [deviceFilter, setDeviceFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'utilization' | 'errors' | 'name'>('utilization');

  const filteredInterfaces = useMemo(() => {
    let result = interfaces.filter((i) => {
      const matchSearch = !search || i.name.toLowerCase().includes(search.toLowerCase()) || i.description.toLowerCase().includes(search.toLowerCase()) || i.deviceName.toLowerCase().includes(search.toLowerCase());
      const matchDevice = deviceFilter === 'all' || i.deviceId === deviceFilter;
      const matchStatus = statusFilter === 'all' || i.status === statusFilter;
      return matchSearch && matchDevice && matchStatus;
    });

    // Sort
    if (sortBy === 'utilization') {
      result = [...result].sort((a, b) => b.utilization - a.utilization);
    } else if (sortBy === 'errors') {
      result = [...result].sort((a, b) => (b.rxErrors + b.txErrors) - (a.rxErrors + a.txErrors));
    } else {
      result = [...result].sort((a, b) => a.name.localeCompare(b.name));
    }

    return result;
  }, [interfaces, search, deviceFilter, statusFilter, sortBy]);

  const stats = useMemo(() => ({
    total: interfaces.length,
    up: interfaces.filter(i => i.status === 'up').length,
    down: interfaces.filter(i => i.status === 'down').length,
    highUtil: interfaces.filter(i => i.utilization > 80).length,
    withErrors: interfaces.filter(i => i.rxErrors + i.txErrors > 0).length,
  }), [interfaces]);

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

  const getUtilBg = (util: number) => {
    if (util > 80) return 'bg-noc-danger';
    if (util > 60) return 'bg-noc-warning';
    return 'bg-noc-success';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Interfaces</h1>
          <p className="text-sm text-noc-text-muted">{stats.total} interfaces monitored</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-noc-text">{stats.total}</p>
          <p className="text-[10px] text-noc-text-muted uppercase">Total</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-noc-success">{stats.up}</p>
          <p className="text-[10px] text-noc-text-muted uppercase">UP</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-noc-danger">{stats.down}</p>
          <p className="text-[10px] text-noc-text-muted uppercase">DOWN</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-noc-warning">{stats.highUtil}</p>
          <p className="text-[10px] text-noc-text-muted uppercase">&gt;80% Util</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-orange-500">{stats.withErrors}</p>
          <p className="text-[10px] text-noc-text-muted uppercase">With Errors</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-noc-surface border border-noc-border rounded-lg p-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-noc-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search interfaces..."
            className="w-full pl-9 pr-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary"
          />
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
            <option value="admin_down">Admin Down</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as 'utilization' | 'errors' | 'name')} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="utilization">Sort: Utilization</option>
            <option value="errors">Sort: Errors</option>
            <option value="name">Sort: Name</option>
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
                <th className="text-right">RX</th>
                <th className="text-right">TX</th>
                <th className="text-right">Errors</th>
                <th className="text-right">Discards</th>
                <th>Utilization</th>
              </tr>
            </thead>
            <tbody>
              {filteredInterfaces.map((iface) => (
                <tr key={iface.id}>
                  <td className="font-mono text-xs text-noc-text font-medium">{iface.name}</td>
                  <td className="text-xs text-noc-text">{iface.deviceName}</td>
                  <td className="text-xs text-noc-text-muted max-w-[150px] truncate">{iface.description}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 text-xs ${iface.status === 'up' ? 'text-noc-success' : 'text-noc-danger'}`}>
                      {iface.status === 'up' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {iface.status === 'admin_down' ? 'ADMIN DOWN' : iface.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{iface.speed}</td>
                  <td className="text-right text-xs text-noc-text font-mono">{formatBytes(iface.rxBytes)}</td>
                  <td className="text-right text-xs text-noc-text font-mono">{formatBytes(iface.txBytes)}</td>
                  <td className="text-right text-xs">
                    <span className={iface.rxErrors + iface.txErrors > 0 ? 'text-noc-warning font-medium' : 'text-noc-text-muted'}>
                      {iface.rxErrors + iface.txErrors}
                    </span>
                  </td>
                  <td className="text-right text-xs">
                    <span className={iface.rxDiscards + iface.txDiscards > 0 ? 'text-orange-500' : 'text-noc-text-muted'}>
                      {iface.rxDiscards + iface.txDiscards}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-noc-bg rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${getUtilBg(iface.utilization)}`} style={{ width: `${iface.utilization}%` }} />
                      </div>
                      <span className={`text-xs font-mono ${getUtilColor(iface.utilization)}`}>{iface.utilization}%</span>
                    </div>
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
