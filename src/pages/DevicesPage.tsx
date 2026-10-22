import { useEffect, useMemo, useRef, useState } from 'react';
import ImportWizard from '../components/ImportWizard';
import apiService from '../services/api';
import { useNavigate } from 'react-router-dom';
import { useDeviceStore, Device, DeviceStatus, DeviceRole } from '../stores/devices';
import { useAuthStore } from '../stores/auth';
import { Plus, Search, Filter, MoreVertical, Edit2, Trash2, Eye, CheckCircle, XCircle, AlertTriangle, Clock, RefreshCw, Upload, Download, WifiOff, FlaskConical, Play } from 'lucide-react';

export default function DevicesPage() {
  const navigate = useNavigate();
  const { devices, sites, deleteDevice, updateDevice, connectionState, isLoading, lastError, lastFetchedAt, fetchAll, enableDemoMode, exitDemoMode } = useDeviceStore();
  const user = useAuthStore((st) => st.user);
  const canWrite = !!user && ['super_admin', 'admin', 'network_engineer'].includes(user.role);
  const [showImport, setShowImport] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const fileDropRef = useRef<HTMLDivElement>(null);

  // Load REAL data from the backend on mount (and after commits).
  useEffect(() => { void fetchAll(); }, [fetchAll]);

  const handleExportCsv = async () => {
    setExporting(true); setExportMsg(null);
    try {
      const blob = await apiService.exportDevicesCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pnmp_device_inventory_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      setExportMsg('CSV exported from live database records.');
    } catch (e: any) {
      setExportMsg(`Export failed: ${e?.message || 'unknown error'}`);
    } finally { setExporting(false); }
  };
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [siteFilter, setSiteFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const filteredDevices = useMemo(() => {
    return devices.filter((d) => {
      const matchSearch = !search || d.displayName.toLowerCase().includes(search.toLowerCase()) || d.hostname.toLowerCase().includes(search.toLowerCase()) || d.managementIp.includes(search);
      const matchStatus = statusFilter === 'all' || d.status === statusFilter;
      const matchSite = siteFilter === 'all' || d.siteId === siteFilter;
      const matchRole = roleFilter === 'all' || d.deviceRole === roleFilter;
      return matchSearch && matchStatus && matchSite && matchRole;
    });
  }, [devices, search, statusFilter, siteFilter, roleFilter]);

  const getStatusIcon = (status: DeviceStatus) => {
    switch (status) {
      case 'up': return <CheckCircle className="w-3.5 h-3.5 text-noc-success" />;
      case 'down': return <XCircle className="w-3.5 h-3.5 text-noc-danger" />;
      case 'warning': return <AlertTriangle className="w-3.5 h-3.5 text-noc-warning" />;
      case 'maintenance': return <Clock className="w-3.5 h-3.5 text-noc-info" />;
      default: return <AlertTriangle className="w-3.5 h-3.5 text-noc-text-muted" />;
    }
  };

  const getStatusClass = (status: DeviceStatus) => {
    switch (status) {
      case 'up': return 'bg-noc-success/10 text-noc-success border-noc-success/20';
      case 'down': return 'bg-noc-danger/10 text-noc-danger border-noc-danger/20';
      case 'warning': return 'bg-noc-warning/10 text-noc-warning border-noc-warning/20';
      case 'maintenance': return 'bg-noc-info/10 text-noc-info border-noc-info/20';
      default: return 'bg-noc-surface-2 text-noc-text-muted';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Devices</h1>
          <p className="text-sm text-noc-text-muted">{filteredDevices.length} of {devices.length} devices</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleExportCsv} disabled={exporting || connectionState === 'demo'} title="Download actual inventory as CSV" className="flex items-center gap-2 px-3 py-2 border border-noc-border text-noc-text-muted hover:text-noc-text text-sm rounded-lg transition-colors">
            <Download className="w-4 h-4" /> {exporting ? 'Exporting…' : 'Export CSV'}
          </button>
          {canWrite && (
            <button onClick={() => setShowImport(true)} disabled={connectionState !== 'live'} title={connectionState === 'live' ? 'Bulk import from Excel' : 'Backend required for import'} className="flex items-center gap-2 px-3 py-2 border border-noc-primary/50 text-noc-primary hover:bg-noc-primary/10 text-sm rounded-lg transition-colors disabled:opacity-40">
              <Upload className="w-4 h-4" /> Import Excel
            </button>
          )}
          <button onClick={() => setShowAddModal(true)} disabled={!canWrite || connectionState !== 'live'} className="flex items-center gap-2 px-3 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50" title={canWrite ? 'Register a new device' : 'Administrator / Network Engineer role required'}>
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        </div>
      </div>

      {/* Connection state banner — never let demo values masquerade as live data */}
      {connectionState === 'disconnected' && (
        <div ref={fileDropRef} className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-noc-danger/10 border border-noc-danger/30">
          <div className="flex items-start gap-2 text-sm text-noc-danger">
            <WifiOff className="w-4 h-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold">DISCONNECTED — backend API unreachable</p>
              <p className="text-xs text-noc-text-muted">{lastError || 'No data is shown because no fabricated values are displayed as live metrics.'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => void fetchAll()} className="px-3 py-1.5 text-xs text-white bg-noc-primary rounded-lg flex items-center gap-1"><RefreshCw className="w-3 h-3" /> Retry</button>
            <button onClick={enableDemoMode} className="px-3 py-1.5 text-xs border border-noc-warning/50 text-noc-warning rounded-lg flex items-center gap-1"><Play className="w-3 h-3" /> Enable DEMO mode</button>
          </div>
        </div>
      )}
      {connectionState === 'demo' && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-noc-warning/15 border border-noc-warning/40">
          <div className="flex items-center gap-2 text-sm text-noc-warning font-semibold uppercase tracking-wide">
            <FlaskConical className="w-4 h-4" /> DEMO MODE — sample data only. NOT live production metrics.
          </div>
          <button onClick={exitDemoMode} className="px-3 py-1.5 text-xs text-white bg-noc-primary rounded-lg">Exit demo &amp; connect</button>
        </div>
      )}
      {connectionState === 'live' && (
        <div className="flex items-center justify-between text-[11px] text-noc-text-muted px-1">
          <span className="flex items-center gap-1"><CheckCircle className="w-3 h-3 text-noc-success" /> LIVE data from backend{lastFetchedAt ? ` · last fetched ${new Date(lastFetchedAt).toLocaleTimeString()}` : ''}</span>
          {exportMsg && <span>{exportMsg}</span>}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-noc-surface border border-noc-border rounded-lg p-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-noc-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search devices..."
            className="w-full pl-9 pr-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-noc-text-muted" />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="all">All Status</option>
            <option value="up">UP</option>
            <option value="down">DOWN</option>
            <option value="warning">WARNING</option>
            <option value="maintenance">MAINTENANCE</option>
          </select>
          <select value={siteFilter} onChange={(e) => setSiteFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="all">All Sites</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="all">All Roles</option>
            <option value="core_switch">Core Switch</option>
            <option value="distribution_switch">Distribution Switch</option>
            <option value="access_switch">Access Switch</option>
            <option value="router">Router</option>
            <option value="firewall">Firewall</option>
            <option value="wireless_controller">Wireless Controller</option>
            <option value="access_point">Access Point</option>
            <option value="server">Server</option>
          </select>
        </div>
      </div>

      {/* Device table */}
      <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Device</th>
                <th>IP Address</th>
                <th>Vendor / Model</th>
                <th>Role</th>
                <th>Site</th>
                <th>CPU</th>
                <th>Memory</th>
                <th>Uptime</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map((device) => (
                <tr key={device.id}>
                  <td>
                    <div className="flex items-center gap-1.5">
                      {getStatusIcon(device.status)}
                      <span className={`text-xs font-medium ${device.status === 'up' ? 'text-noc-success' : device.status === 'down' ? 'text-noc-danger' : device.status === 'warning' ? 'text-noc-warning' : 'text-noc-info'}`}>
                        {device.status.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div>
                      <p className="text-sm font-medium text-noc-text">{device.displayName}</p>
                      <p className="text-[10px] text-noc-text-muted font-mono">{device.hostname}</p>
                    </div>
                  </td>
                  <td className="font-mono text-xs text-noc-text-muted">{device.managementIp}</td>
                  <td>
                    <p className="text-xs text-noc-text">{device.vendor}</p>
                    <p className="text-[10px] text-noc-text-muted">{device.model}</p>
                  </td>
                  <td>
                    <span className="text-xs text-noc-text-muted">{device.deviceRole.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{device.siteName}</td>
                  <td>
                    <span className={`text-xs ${device.cpu > 70 ? 'text-noc-danger' : device.cpu > 50 ? 'text-noc-warning' : 'text-noc-text-muted'}`}>
                      {device.cpu >= 0 ? `${device.cpu}%` : '—'}
                    </span>
                  </td>
                  <td>
                    <span className={`text-xs ${device.memory > 80 ? 'text-noc-danger' : device.memory > 60 ? 'text-noc-warning' : 'text-noc-text-muted'}`}>
                      {device.memory >= 0 ? `${device.memory}%` : '—'}
                    </span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{device.uptime}</td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button onClick={() => navigate(`/devices/${device.id}`)} className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-primary transition-colors" title="View Details">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setEditingDevice(device)} className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-warning transition-colors" title="Edit">
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-success transition-colors" title="Test Connection">
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setShowDeleteConfirm(device.id)} className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-danger transition-colors" title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {isLoading && filteredDevices.length === 0 && (
          <div className="p-8 text-center">
            <RefreshCw className="w-6 h-6 mx-auto mb-2 text-noc-primary animate-spin" />
            <p className="text-sm text-noc-text-muted">Loading inventory from backend…</p>
          </div>
        )}
        {!isLoading && connectionState === 'disconnected' && (
          <div className="p-8 text-center">
            <WifiOff className="w-6 h-6 mx-auto mb-2 text-noc-danger" />
            <p className="text-sm text-noc-text-muted">No data available while disconnected. Check that the backend is running (scripts\start-backend.ps1) and press Retry above.</p>
          </div>
        )}
        {!isLoading && connectionState === 'live' && devices.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-sm text-noc-text-muted">Inventory is empty. Use “Import Excel” to bulk-register devices or “Add Device” to create one.</p>
          </div>
        )}
        {!isLoading && devices.length > 0 && filteredDevices.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-sm text-noc-text-muted">No devices found matching your filters.</p>
          </div>
        )}
      </div>

      {showImport && (
        <ImportWizard onClose={() => setShowImport(false)} onCommitted={() => void fetchAll()} />
      )}

      {/* Add/Edit Device Modal */}
      {(showAddModal || editingDevice) && (
        <DeviceModal
          device={editingDevice}
          sites={sites}
          onClose={() => { setShowAddModal(false); setEditingDevice(null); }}
          onSave={() => { setShowAddModal(false); setEditingDevice(null); }}
        />
      )}

      {/* Delete confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-noc-surface border border-noc-border rounded-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-noc-text mb-2">Delete Device</h3>
            <p className="text-sm text-noc-text-muted mb-4">Are you sure you want to delete this device? This action cannot be undone.</p>
            <div className="flex items-center gap-3 justify-end">
              <button onClick={() => setShowDeleteConfirm(null)} className="px-4 py-2 text-sm text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={() => { deleteDevice(showDeleteConfirm); setShowDeleteConfirm(null); }} className="px-4 py-2 text-sm text-white bg-noc-danger hover:bg-noc-danger/90 rounded-lg transition-colors">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Device Modal Component
function DeviceModal({ device, sites, onClose, onSave }: { device: Device | null; sites: { id: string; name: string }[]; onClose: () => void; onSave: () => void }) {
  const { addDevice, updateDevice } = useDeviceStore();
  const [form, setForm] = useState({
    hostname: device?.hostname || '',
    displayName: device?.displayName || '',
    managementIp: device?.managementIp || '',
    vendor: device?.vendor || '',
    model: device?.model || '',
    serialNumber: device?.serialNumber || '',
    deviceType: device?.deviceType || '',
    deviceRole: device?.deviceRole || 'access_switch' as DeviceRole,
    siteId: device?.siteId || sites[0]?.id || '',
    location: device?.location || '',
    description: device?.description || '',
    monitoringEnabled: device?.monitoringEnabled ?? true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (device) {
      updateDevice(device.id, form);
    } else {
      addDevice({
        ...form,
        id: Date.now().toString(),
        siteName: sites.find(s => s.id === form.siteId)?.name || '',
        status: 'unknown' as DeviceStatus,
        firmwareVersion: '',
        macAddress: '',
        uptime: '-',
        cpu: 0,
        memory: 0,
        temperature: 0,
        lastSeen: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      });
    }
    onSave();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-noc-surface border border-noc-border rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-noc-text mb-4">{device ? 'Edit Device' : 'Add New Device'}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Display Name *</label>
              <input type="text" required value={form.displayName} onChange={(e) => setForm({ ...form, displayName: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Hostname *</label>
              <input type="text" required value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Management IP *</label>
              <input type="text" required value={form.managementIp} onChange={(e) => setForm({ ...form, managementIp: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="10.0.0.1" />
            </div>
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Vendor *</label>
              <input type="text" required value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="Aruba, Cisco, Fortinet..." />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Model</label>
              <input type="text" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Serial Number</label>
              <input type="text" value={form.serialNumber} onChange={(e) => setForm({ ...form, serialNumber: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Device Type</label>
              <input type="text" value={form.deviceType} onChange={(e) => setForm({ ...form, deviceType: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="Switch, Router, Firewall..." />
            </div>
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Device Role</label>
              <select value={form.deviceRole} onChange={(e) => setForm({ ...form, deviceRole: e.target.value as DeviceRole })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                <option value="core_switch">Core Switch</option>
                <option value="distribution_switch">Distribution Switch</option>
                <option value="access_switch">Access Switch</option>
                <option value="router">Router</option>
                <option value="firewall">Firewall</option>
                <option value="wireless_controller">Wireless Controller</option>
                <option value="access_point">Access Point</option>
                <option value="server">Server</option>
                <option value="load_balancer">Load Balancer</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Site *</label>
              <select required value={form.siteId} onChange={(e) => setForm({ ...form, siteId: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1">Location</label>
              <input type="text" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="Rack, Floor, Room..." />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-noc-text-muted mb-1">Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary resize-none" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="monitoring" checked={form.monitoringEnabled} onChange={(e) => setForm({ ...form, monitoringEnabled: e.target.checked })} className="rounded border-noc-border" />
            <label htmlFor="monitoring" className="text-sm text-noc-text">Enable Monitoring</label>
          </div>
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-noc-border">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg transition-colors">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 text-sm text-white bg-noc-primary hover:bg-noc-primary/90 rounded-lg transition-colors">
              {device ? 'Update Device' : 'Add Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
